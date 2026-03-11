import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScreenerService, type MacroAssumptions } from '@/services/api';
import { Settings2, Loader2, Sparkles } from 'lucide-react';

interface StressTestSidebarProps {
    ticker: string;
    defaultMacros: MacroAssumptions;
    onSimulate: (simulatedAnalysis: any) => void;
}

export function StressTestSidebar({ ticker, defaultMacros, onSimulate }: StressTestSidebarProps) {
    const [selic, setSelic] = useState(defaultMacros.selic_used?.toString() || "10.5");
    const [ipca, setIpca] = useState(defaultMacros.ipca_used?.toString() || "4.5");
    const [pib, setPib] = useState(defaultMacros.pib_used?.toString() || "2.0");
    const [loading, setLoading] = useState(false);
    const [open, setOpen] = useState(false); // Mobile toggle

    const handleSimulate = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        try {
            const payload = {
                selic_esperada: parseFloat(selic),
                ipca_esperado: parseFloat(ipca),
                pib_esperado: parseFloat(pib)
            };

            const newAnalysis = await ScreenerService.runStressTest(ticker, payload);
            onSimulate(newAnalysis); // Pass the raw new JSON payload up to Dashboard

        } catch (err) {
            console.error(err);
            alert("Houve um erro rodando a simulação de Stress Test. Consulte os logs do console.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <>
            {/* Modulo Desktop */}
            <div className="fixed right-6 bottom-6 z-50 flex flex-col items-end">

                {/* Toggle animado */}
                {!open && (
                    <Button
                        onClick={() => setOpen(true)}
                        variant="default"
                        className="bg-cyan-600 hover:bg-cyan-500 text-white font-bold rounded-full shadow-2xl h-14 w-14 p-0 animate-bounce"
                    >
                        <Settings2 className="w-6 h-6" />
                    </Button>
                )}

                {/* Form Card */}
                {open && (
                    <Card className="w-80 bg-slate-900 border-cyan-800 shadow-2xl shadow-cyan-900/20 animate-in slide-in-from-bottom-5">
                        <CardHeader className="pb-4 relative">
                            <Button
                                variant="ghost"
                                size="sm"
                                className="absolute right-2 top-2 text-slate-400 hover:text-white"
                                onClick={() => setOpen(false)}
                            >
                                X
                            </Button>
                            <CardTitle className="text-lg flex items-center text-cyan-400">
                                <Sparkles className="w-4 h-4 mr-2" />
                                Máquina de Cenários
                            </CardTitle>
                            <CardDescription className="text-slate-400 text-xs">
                                Modifique os índices macroeconômicos e recalcule {ticker} em tempo real sem persistir no banco.
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            <form onSubmit={handleSimulate} className="space-y-4">

                                <div className="space-y-1.5">
                                    <label className="text-xs font-semibold text-slate-300">Selic Esperada (%)</label>
                                    <Input
                                        type="number"
                                        step="0.1"
                                        value={selic}
                                        onChange={e => setSelic(e.target.value)}
                                        className="bg-slate-800 border-slate-700 text-slate-100 placeholder:text-slate-500 h-9"
                                        required
                                    />
                                </div>

                                <div className="space-y-1.5">
                                    <label className="text-xs font-semibold text-slate-300">IPCA Esperado (%)</label>
                                    <Input
                                        type="number"
                                        step="0.1"
                                        value={ipca}
                                        onChange={e => setIpca(e.target.value)}
                                        className="bg-slate-800 border-slate-700 text-slate-100 placeholder:text-slate-500 h-9"
                                        required
                                    />
                                </div>

                                <div className="space-y-1.5">
                                    <label className="text-xs font-semibold text-slate-300">PIB Projetado (%)</label>
                                    <Input
                                        type="number"
                                        step="0.1"
                                        value={pib}
                                        onChange={e => setPib(e.target.value)}
                                        className="bg-slate-800 border-slate-700 text-slate-100 placeholder:text-slate-500 h-9"
                                        required
                                    />
                                </div>

                                <Button
                                    type="submit"
                                    className="w-full bg-cyan-600 hover:bg-cyan-500 text-white mt-2"
                                    disabled={loading}
                                >
                                    {loading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Settings2 className="w-4 h-4 mr-2" />}
                                    {loading ? 'Calculando...' : 'Rodar Stress Test'}
                                </Button>

                            </form>
                        </CardContent>
                    </Card>
                )}
            </div>
        </>
    );
}
