import { useState } from 'react';
import { AdminService, ScreenerService } from '@/services/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Database, RefreshCcw, Loader2, Info } from 'lucide-react';

export function AdminSync() {
    const [loadingCompanies, setLoadingCompanies] = useState(false);
    const [loadingScreener, setLoadingScreener] = useState(false);
    const [status, setStatus] = useState<{ message: string, type: 'success' | 'error' | 'info' } | null>(null);

    const [macro, setMacro] = useState({
        selic_esperada: 10.75,
        ipca_esperado: 4.5,
        pib_esperado: 2.0
    });

    const handleSyncCompanies = async () => {
        setLoadingCompanies(true);
        setStatus({ message: "Iniciando sincronização de ativos...", type: 'info' });
        try {
            const res = await AdminService.syncCompanies();
            setStatus({ message: `Sucesso: ${res.message} (${res.total_processed} ativos)`, type: 'success' });
        } catch (err) {
            setStatus({ message: "Erro: Falha ao sincronizar com a BRAPI.", type: 'error' });
        } finally {
            setLoadingCompanies(false);
        }
    };

    const handleSyncScreener = async () => {
        setLoadingScreener(true);
        setStatus({ message: "Iniciando motor quantitativo...", type: 'info' });
        try {
            const res = await ScreenerService.syncScreener(macro);
            setStatus({ message: res.message, type: 'success' });
        } catch (err) {
            setStatus({ message: "Erro ao iniciar motor de análise.", type: 'error' });
        } finally {
            setLoadingScreener(false);
        }
    };

    return (
        <div className="container mx-auto py-8 px-4 max-w-4xl space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="flex justify-between items-start">
                <div>
                    <h1 className="text-3xl font-bold text-slate-100 flex items-center gap-3">
                        <Database className="w-8 h-8 text-cyan-400" />
                        Gerenciamento de Dados
                    </h1>
                    <p className="text-slate-400 mt-2">Sincronize as bases de dados e dispare o motor de inteligência quantitativa.</p>
                </div>

                {status && (
                    <div className={`flex items-center gap-2 px-4 py-2 rounded-lg border ${status.type === 'success' ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' :
                            status.type === 'error' ? 'bg-rose-500/10 border-rose-500/20 text-rose-400' :
                                'bg-blue-500/10 border-blue-500/20 text-blue-400'
                        }`}>
                        <Info className="w-4 h-4" />
                        <span className="text-sm font-medium">{status.message}</span>
                    </div>
                )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* SYNC COMPANIES */}
                <Card className="bg-slate-900 border-slate-800">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <RefreshCcw className={`w-5 h-5 ${loadingCompanies ? 'animate-spin' : ''} text-emerald-500`} />
                            Base de Ativos B3
                        </CardTitle>
                        <CardDescription>Atualiza a listagem oficial de tickers via BRAPI.</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <Button
                            onClick={handleSyncCompanies}
                            disabled={loadingCompanies}
                            className="w-full bg-emerald-600 hover:bg-emerald-500 text-white"
                        >
                            {loadingCompanies ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                            Sincronizar Tickers
                        </Button>
                    </CardContent>
                </Card>

                {/* SYNC SCREENER */}
                <Card className="bg-slate-900 border-slate-800">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <RefreshCcw className={`w-5 h-5 ${loadingScreener ? 'animate-spin' : ''} text-cyan-500`} />
                            Motor Quantitativo
                        </CardTitle>
                        <CardDescription>Análise total do mercado usando premissas macro.</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="grid grid-cols-3 gap-2 text-xs">
                            <div className="space-y-1.5">
                                <label className="text-slate-500 uppercase font-bold">SELIC %</label>
                                <Input
                                    type="number"
                                    value={macro.selic_esperada}
                                    onChange={e => setMacro({ ...macro, selic_esperada: parseFloat(e.target.value) })}
                                    className="bg-slate-950 border-slate-800 h-8 font-mono"
                                />
                            </div>
                            <div className="space-y-1.5">
                                <label className="text-slate-500 uppercase font-bold">IPCA %</label>
                                <Input
                                    type="number"
                                    value={macro.ipca_esperado}
                                    onChange={e => setMacro({ ...macro, ipca_esperado: parseFloat(e.target.value) })}
                                    className="bg-slate-950 border-slate-800 h-8 font-mono"
                                />
                            </div>
                            <div className="space-y-1.5">
                                <label className="text-slate-500 uppercase font-bold">PIB %</label>
                                <Input
                                    type="number"
                                    value={macro.pib_esperado}
                                    onChange={e => setMacro({ ...macro, pib_esperado: parseFloat(e.target.value) })}
                                    className="bg-slate-950 border-slate-800 h-8 font-mono"
                                />
                            </div>
                        </div>
                        <Button
                            onClick={handleSyncScreener}
                            disabled={loadingScreener}
                            className="w-full bg-cyan-600 hover:bg-cyan-500 text-white"
                        >
                            {loadingScreener ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                            Executar Full Sync
                        </Button>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
