import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { ScreenerService, type StockEvaluationRecord } from '@/services/api';
import { GlobalScoreBadge } from '@/components/qfa/GlobalScoreBadge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { AlertCircle, ArrowRight, Activity } from 'lucide-react';

const SECTORS = [
    "Financial Services",
    "Utilities",
    "Technology",
    "Energy",
    "Basic Materials",
    "Consumer Defensive"
];

export function ScreenerHome() {
    const [sector, setSector] = useState("Financial Services");
    const [data, setData] = useState<StockEvaluationRecord[]>([]);
    const [loading, setLoading] = useState(false);
    const [warning, setWarning] = useState<string | null>(null);

    useEffect(() => {
        async function loadData() {
            setLoading(true);
            try {
                const result = await ScreenerService.getSectorRanking(sector, 15);
                setData(result.data);
                setWarning(result.warning);
            } catch (err) {
                console.error(err);
                setWarning("Erro ao carregar ranking. Verifique se a API está online.");
            } finally {
                setLoading(false);
            }
        }
        loadData();
    }, [sector]);

    const latestMeta = data.length > 0 ? data[0].metadata : null;

    return (
        <div className="container mx-auto py-8 px-4 max-w-6xl space-y-8 animate-in fade-in duration-500">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                    <h1 className="text-4xl font-extrabold tracking-tight bg-gradient-to-r from-emerald-400 to-cyan-500 bg-clip-text text-transparent">
                        Terminal QFA
                    </h1>
                    <p className="text-slate-400 mt-1">Ranking quantitativo do mercado de ações Brasileiro.</p>
                </div>

                <div className="flex items-center gap-4">
                    <Select value={sector} onValueChange={setSector}>
                        <SelectTrigger className="w-[200px] border-slate-700 bg-slate-900">
                            <SelectValue placeholder="Selecione o Setor" />
                        </SelectTrigger>
                        <SelectContent className="bg-slate-900 border-slate-700">
                            {SECTORS.map(s => (
                                <SelectItem key={s} value={s}>{s}</SelectItem>
                            ))}
                        </SelectContent>
                    </Select>
                </div>
            </div>

            {warning && (
                <div className="bg-amber-500/10 border border-amber-500/20 text-amber-400 px-4 py-3 rounded-lg flex items-center gap-3">
                    <AlertCircle className="w-5 h-5 flex-shrink-0" />
                    <p className="text-sm font-medium">{warning}</p>
                </div>
            )}

            {latestMeta && (
                <Card className="bg-slate-900 border-slate-800">
                    <CardHeader className="py-4">
                        <CardTitle className="text-sm text-slate-400 flex items-center gap-2">
                            <Activity className="w-4 h-4 text-emerald-500" />
                            Base Macro Utilizada na Avaliação (Data: {latestMeta.last_updated})
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="flex gap-8 text-sm py-0 pb-4">
                        <div><span className="text-slate-500">Selic Projetada:</span> <span className="text-slate-200 font-mono ml-1">{latestMeta.macro_assumptions.selic_used}%</span></div>
                        <div><span className="text-slate-500">IPCA Projetado:</span> <span className="text-slate-200 font-mono ml-1">{latestMeta.macro_assumptions.ipca_used}%</span></div>
                        <div><span className="text-slate-500">PIB Projetado:</span> <span className="text-slate-200 font-mono ml-1">{latestMeta.macro_assumptions.pib_used}%</span></div>
                    </CardContent>
                </Card>
            )}

            {loading ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {[1, 2, 3, 4, 5, 6].map(i => (
                        <div key={i} className="h-32 bg-slate-800/50 rounded-xl animate-pulse"></div>
                    ))}
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {data.map((record) => {
                        const analysis = record.analysis;
                        const industry = analysis.raw_data_summary.info.industry;
                        return (
                            <Link to={`/stock/${analysis.ticker}`} key={analysis.ticker}>
                                <Card className="bg-slate-900 border-slate-800 hover:border-slate-600 transition-colors group cursor-pointer h-full">
                                    <CardContent className="p-5 flex flex-col justify-between h-full">
                                        <div className="flex justify-between items-start mb-4">
                                            <div>
                                                <h2 className="text-2xl font-bold text-slate-100 group-hover:text-cyan-400 transition-colors">{analysis.ticker}</h2>
                                                <p className="text-xs text-slate-400 truncate max-w-[150px]">{industry}</p>
                                            </div>
                                            <GlobalScoreBadge score={analysis.global_score} size="md" />
                                        </div>

                                        <div className="flex justify-between items-end mt-4">
                                            <div className="flex gap-2 text-xs">
                                                {analysis.flags.bankruptcy_risk && <span className="bg-rose-500/10 text-rose-400 px-2 py-1 rounded">Risco Z-Score</span>}
                                            </div>
                                            <ArrowRight className="w-5 h-5 text-slate-600 group-hover:text-cyan-400 transition-colors" />
                                        </div>
                                    </CardContent>
                                </Card>
                            </Link>
                        )
                    })}
                </div>
            )}
        </div>
    );
}
