import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ScreenerService, AnalysisService, type StockEvaluationRecord } from '@/services/api';
import { GlobalScoreBadge, getScoreColor } from '@/components/qfa/GlobalScoreBadge';
import { QfaRadarChart } from '@/components/qfa/QfaRadarChart';
import { InfoTooltip } from '@/components/qfa/InfoTooltip';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ArrowLeft, AlertOctagon, TrendingUp, DollarSign, Activity, ShieldAlert, RefreshCw, CheckCircle2, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { StressTestSidebar } from '@/components/qfa/StressTestSidebar';

export function ActionDashboard() {
    const { ticker } = useParams<{ ticker: string }>();
    const [record, setRecord] = useState<StockEvaluationRecord | null>(null);
    const [loading, setLoading] = useState(false);
    const [errorNotFound, setErrorNotFound] = useState(false);

    // Async Task State
    const [taskStatus, setTaskStatus] = useState<'idle' | 'processing' | 'done' | 'failed'>('idle');
    const [isSimulating, setIsSimulating] = useState(false);

    const loadData = async () => {
        if (!ticker) return;
        setLoading(true);
        setErrorNotFound(false);
        try {
            const response = await ScreenerService.getTickerData(ticker);
            setRecord(response);
            setIsSimulating(false);
        } catch (err: any) {
            if (err.response?.status === 404) {
                setErrorNotFound(true);
            }
        } finally {
            setLoading(false);
        }
    };

    const handleBackgroundRefresh = async () => {
        if (!ticker || !record) return;
        setTaskStatus('processing');
        try {
            const { task_id } = await AnalysisService.startAnalysis(ticker, {
                selic_esperada: record.metadata.macro_assumptions.selic_used || 10.75,
                ipca_esperado: record.metadata.macro_assumptions.ipca_used || 4.5,
                pib_esperado: record.metadata.macro_assumptions.pib_used || 2.0
            });

            // Poll for result
            const pollInterval = setInterval(async () => {
                try {
                    const result = await AnalysisService.getAnalysisResult(task_id);
                    if (result.status === 'success') {
                        clearInterval(pollInterval);
                        setTaskStatus('done');
                        loadData(); // Reload to get the new persistent data
                        setTimeout(() => setTaskStatus('idle'), 3000);
                    } else if (result.status === 'failed') {
                        clearInterval(pollInterval);
                        setTaskStatus('failed');
                        setTimeout(() => setTaskStatus('idle'), 5000);
                    }
                } catch (e) {
                    // Still processing or error
                }
            }, 2000);

        } catch (err) {
            setTaskStatus('failed');
            setTimeout(() => setTaskStatus('idle'), 5000);
        }
    };

    useEffect(() => {
        loadData();
    }, [ticker]);

    if (loading && !record) {
        return (
            <div className="container mx-auto py-12 px-4 max-w-6xl flex justify-center mt-20">
                <div className="w-12 h-12 border-4 border-slate-700 border-t-cyan-500 rounded-full animate-spin"></div>
            </div>
        );
    }

    if (errorNotFound || !record) {
        return (
            <div className="container mx-auto py-12 px-4 max-w-6xl text-center mt-20">
                <h1 className="text-4xl font-bold text-slate-100 mb-4">Ticker não encontrado</h1>
                <p className="text-slate-400 mb-8">Nenhuma análise quantitativa disponível para {ticker}.</p>
                <Link to="/">
                    <Button variant="outline" className="border-slate-700 text-slate-300">
                        <ArrowLeft className="w-4 h-4 mr-2" />
                        Voltar ao Screener
                    </Button>
                </Link>
            </div>
        );
    }

    const analysis = record.analysis;
    const raw = analysis.raw_data_summary;
    const flags = analysis.flags;

    // For Real-time updates from Stress Test
    const handleSimulationComplete = (simulatedAnalysis: any) => {
        setRecord((prev) => prev ? { ...prev, analysis: simulatedAnalysis } : null);
        setIsSimulating(true);
    };

    // Radar Data Mapping
    const radarData = [
        { subject: 'Solvência', A: (raw.solvency.current_ratio && raw.solvency.current_ratio > 1.5) ? 9 : 5, fullMark: 10 },
        { subject: 'Rentabilidade', A: raw.profitability.roic ? Math.min(10, Math.max(0, raw.profitability.roic * 100)) : 5, fullMark: 10 },
        { subject: 'Crescimento', A: raw.growth.earnings_growth ? Math.min(10, Math.max(0, raw.growth.earnings_growth * 100 + 4)) : 4, fullMark: 10 },
        { subject: 'Forensic Risk', A: flags.manipulation_risk ? 2 : (flags.bankruptcy_risk ? 4 : 9), fullMark: 10 },
        { subject: 'Valuation', A: raw.valuation.price_to_book ? (raw.valuation.price_to_book < 1.5 ? 9 : 4) : 5, fullMark: 10 },
    ];

    return (
        <div className="container mx-auto py-8 px-4 max-w-7xl animate-in fade-in duration-700 pb-20">

            {/* HEADER NAV */}
            <div className="flex items-center justify-between mb-8">
                <Link to="/" className="text-slate-400 hover:text-cyan-400 transition-colors flex items-center">
                    <ArrowLeft className="w-5 h-5 mr-2" />
                    Voltar as Análises
                </Link>
                {isSimulating && (
                    <span className="bg-cyan-500/20 text-cyan-400 px-3 py-1 rounded text-sm font-semibold animate-pulse border border-cyan-500/30">
                        • MODO SIMULAÇÃO (STRESS TEST)
                    </span>
                )}
            </div>

            {/* KILL SWITCH BANNERS */}
            {flags.bankruptcy_risk && (
                <div className="bg-rose-500/10 border-l-4 border-rose-500 p-4 mb-6 rounded-r-md flex items-start gap-4">
                    <AlertOctagon className="w-6 h-6 text-rose-500 mt-0.5" />
                    <div>
                        <h3 className="text-rose-400 font-bold">Alerta de Falência (Altman Z-Score)</h3>
                        <p className="text-slate-300 text-sm mt-1">
                            O Z-Score desta empresa está na zona de stress financeiro severo (Z = {raw.forensic_scores.altman_z_score?.toFixed(2)}).
                            O algoritmo limitou artificialmente todas as notas longas como mecanismo de proteção.
                        </p>
                    </div>
                </div>
            )}

            {flags.manipulation_risk && (
                <div className="bg-amber-500/10 border-l-4 border-amber-500 p-4 mb-6 rounded-r-md flex items-start gap-4">
                    <ShieldAlert className="w-6 h-6 text-amber-500 mt-0.5" />
                    <div>
                        <h3 className="text-amber-400 font-bold">Risco de Manipulação Contábil (Beneish M-Score)</h3>
                        <p className="text-slate-300 text-sm mt-1">
                            Detectada possível manipulação de lucros. Resultados financeiros devem ser lidos com ceticismo.
                        </p>
                    </div>
                </div>
            )}

            <div className="grid grid-cols-1 xl:grid-cols-12 gap-8">

                {/* LEFT COLUMN: Main Score & Radar */}
                <div className="xl:col-span-4 flex flex-col gap-6">
                    <Card className="bg-slate-900 border-slate-800 shadow-2xl overflow-hidden relative">
                        <div className={cn("absolute top-0 left-0 w-full h-1.5", getScoreColor(analysis.global_score))}></div>
                        <CardContent className="pt-8 pb-8 flex flex-col items-center text-center">
                            <h1 className="text-6xl font-black text-slate-100 mb-2">{analysis.ticker}</h1>
                            <p className="text-sm font-semibold text-slate-400 mb-8 uppercase tracking-widest">{raw.info.industry}</p>

                            <div className="relative">
                                <svg className="w-48 h-48 transform -rotate-90">
                                    <circle cx="96" cy="96" r="88" stroke="currentColor" strokeWidth="8" fill="transparent" className="text-slate-800" />
                                    <circle
                                        cx="96" cy="96" r="88"
                                        stroke="currentColor"
                                        strokeWidth="8"
                                        fill="transparent"
                                        strokeDasharray={2 * Math.PI * 88}
                                        strokeDashoffset={2 * Math.PI * 88 * (1 - analysis.global_score / 10)}
                                        className={getScoreColor(analysis.global_score).split(' ')[0].replace('bg-', 'text-')}
                                        strokeLinecap="round"
                                    />
                                </svg>
                                <div className="absolute inset-0 flex flex-col items-center justify-center">
                                    <span className="text-5xl font-black text-slate-100">{analysis.global_score.toFixed(1)}</span>
                                    <span className="text-xs text-slate-400 mt-1 font-semibold uppercase">Global Score</span>
                                </div>
                            </div>

                            <div className="mt-8 w-full px-6">
                                <Button
                                    variant="outline"
                                    className={cn(
                                        "w-full border-slate-800 bg-slate-950/50 hover:bg-slate-800 text-slate-400 text-xs h-9 gap-2",
                                        taskStatus === 'done' && "text-emerald-500 border-emerald-500/20",
                                        taskStatus === 'failed' && "text-rose-500 border-rose-500/20"
                                    )}
                                    onClick={handleBackgroundRefresh}
                                    disabled={taskStatus === 'processing'}
                                >
                                    {taskStatus === 'processing' ? <Loader2 className="w-3 h-3 animate-spin" /> :
                                        taskStatus === 'done' ? <CheckCircle2 className="w-3 h-3" /> :
                                            <RefreshCw className="w-3 h-3" />}

                                    {taskStatus === 'processing' ? 'Recalculando...' :
                                        taskStatus === 'done' ? 'Atualizado!' :
                                            taskStatus === 'failed' ? 'Erro na Fila' :
                                                'Atualizar na Base'}
                                </Button>
                            </div>
                        </CardContent>
                    </Card>

                    <Card className="bg-slate-900 border-slate-800 shadow-xl">
                        <CardHeader className="pb-2">
                            <CardTitle className="text-sm text-slate-400">Equilíbrio Estrutural</CardTitle>
                        </CardHeader>
                        <CardContent className="px-0">
                            <QfaRadarChart data={radarData} height={250} />
                        </CardContent>
                    </Card>
                </div>

                {/* RIGHT COLUMN: Fundamentals & Projections */}
                <div className="xl:col-span-8 flex flex-col gap-6">

                    {/* Projections Row */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        {Object.entries(analysis.scores).map(([horizon, score]) => (
                            <Card key={horizon} className="bg-slate-900/50 border-slate-800 backdrop-blur">
                                <CardContent className="p-4 flex flex-col items-center justify-center text-center">
                                    <span className="text-xs text-slate-500 font-bold uppercase mb-2">Visão {horizon.replace('_', ' ')}</span>
                                    <GlobalScoreBadge score={score} size="lg" className="w-full justify-center" />
                                </CardContent>
                            </Card>
                        ))}
                    </div>

                    {/* Fundamentals Grid */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-4">

                        <Card className="bg-slate-900 border-slate-800">
                            <CardHeader className="pb-4 flex flex-row items-center justify-between">
                                <CardTitle className="text-lg flex items-center text-slate-200">
                                    <Activity className="w-5 h-5 mr-2 text-cyan-500" /> Rentabilidade
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="flex justify-between items-center pb-3 border-b border-slate-800">
                                    <span className="text-slate-400 text-sm">
                                        ROE
                                        <InfoTooltip content="Return on Equity: Mede o lucro líquido como porcentagem do patrimônio líquido. Acima de 15% é considerado excelente." />
                                    </span>
                                    <span className="text-slate-100 font-mono">{(raw.profitability.roe ? (raw.profitability.roe * 100).toFixed(1) : 0)}%</span>
                                </div>
                                <div className="flex justify-between items-center pb-3 border-b border-slate-800">
                                    <span className="text-slate-400 text-sm">
                                        ROIC
                                        <InfoTooltip content="Return on Invested Capital: Mostra a eficiência da alocação de capital da empresa. O ROIC idealmente deve ser superior à taxa Selic." />
                                    </span>
                                    <span className="text-slate-100 font-mono">{(raw.profitability.roic ? (raw.profitability.roic * 100).toFixed(1) : 0)}%</span>
                                </div>
                            </CardContent>
                        </Card>

                        <Card className="bg-slate-900 border-slate-800">
                            <CardHeader className="pb-4 flex flex-row items-center justify-between">
                                <CardTitle className="text-lg flex items-center text-slate-200">
                                    <ShieldAlert className="w-5 h-5 mr-2 text-indigo-500" /> Solvência
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="flex justify-between items-center pb-3 border-b border-slate-800">
                                    <span className="text-slate-400 text-sm">
                                        Liquidez Corrente
                                        <InfoTooltip content="Capacidade de pagar obrigações de curto prazo. Valores menores que 1 indicam perigo imediato de fluxo de caixa." />
                                    </span>
                                    <span className="text-slate-100 font-mono">{raw.solvency.current_ratio?.toFixed(2) || 'N/A'}</span>
                                </div>
                                <div className="flex justify-between items-center pb-3 border-b border-slate-800">
                                    <span className="text-slate-400 text-sm">
                                        Dívida Líq / EBITDA
                                        <InfoTooltip content="Quantos anos a empresa levaria para pagar sua dívida com sua geração de caixa operacional. Um teto seguro costuma ser 3.0x." />
                                    </span>
                                    <span className="text-slate-100 font-mono">{raw.solvency.net_debt_to_ebitda?.toFixed(2) || 'N/A'}x</span>
                                </div>
                            </CardContent>
                        </Card>

                        <Card className="bg-slate-900 border-slate-800">
                            <CardHeader className="pb-4 flex flex-row items-center justify-between">
                                <CardTitle className="text-lg flex items-center text-slate-200">
                                    <TrendingUp className="w-5 h-5 mr-2 text-emerald-500" /> Crescimento
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="flex justify-between items-center pb-3 border-b border-slate-800">
                                    <span className="text-slate-400 text-sm">
                                        Crescimento Receita YoY
                                        <InfoTooltip content="Variação percentual na receita total frente ao ano anterior (Year-over-Year)." />
                                    </span>
                                    <span className="text-slate-100 font-mono">{(raw.growth.revenue_growth ? (raw.growth.revenue_growth * 100).toFixed(1) : 0)}%</span>
                                </div>
                                <div className="flex justify-between items-center pb-3 border-b border-slate-800">
                                    <span className="text-slate-400 text-sm">
                                        Crescimento Lucro YoY
                                        <InfoTooltip content="Aumento ou queda do Lucro Líquido gerado em comparação bruta anual." />
                                    </span>
                                    <span className="text-slate-100 font-mono">{(raw.growth.earnings_growth ? (raw.growth.earnings_growth * 100).toFixed(1) : 0)}%</span>
                                </div>
                            </CardContent>
                        </Card>

                        <Card className="bg-slate-900 border-slate-800">
                            <CardHeader className="pb-4 flex flex-row items-center justify-between">
                                <CardTitle className="text-lg flex items-center text-slate-200">
                                    <DollarSign className="w-5 h-5 mr-2 text-amber-500" /> Valuation
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="flex justify-between items-center pb-3 border-b border-slate-800">
                                    <span className="text-slate-400 text-sm">
                                        Preço / Valor Patrimonial
                                        <InfoTooltip content="P/VP (Price to Book). Avalia se a ação está cara frente ao que a empresa de fato 'tem' em patrimônio líquido. Menor que 1 significa desconto patrimonial." />
                                    </span>
                                    <span className="text-slate-100 font-mono">{raw.valuation.price_to_book?.toFixed(2) || 'N/A'}</span>
                                </div>
                                <div className="flex justify-between items-center pb-3 border-b border-slate-800">
                                    <span className="text-slate-400 text-sm">
                                        Fluxo de Caixa Livre / LL
                                        <InfoTooltip content="Mede a qualidade do lucro líquido. Indica quanto do lucro reportado realmente virou 'dinheiro no caixa' para a empresa usar livremente." />
                                    </span>
                                    <span className="text-slate-100 font-mono">{raw.cash_flow.operating_cash_flow_to_net_income?.toFixed(2) || 'N/A'}</span>
                                </div>
                            </CardContent>
                        </Card>

                    </div>
                </div>
            </div>

            {/* Absolute Sandbox Form Hook */}
            <StressTestSidebar ticker={analysis.ticker} onSimulate={handleSimulationComplete} defaultMacros={record.metadata.macro_assumptions} />
        </div>
    );
}
