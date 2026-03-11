import React from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Target, AlertTriangle, XOctagon, FileText } from 'lucide-react';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';

export function Methodology() {
    return (
        <div className="container mx-auto py-8 px-4 max-w-4xl space-y-8 animate-in fade-in duration-500 pb-20 text-slate-200">

            <div className="flex flex-col gap-2 border-b border-slate-800 pb-6">
                <h1 className="text-4xl font-extrabold tracking-tight bg-gradient-to-r from-emerald-400 to-cyan-500 bg-clip-text text-transparent">
                    A Metodologia QFA
                </h1>
                <p className="text-slate-400">
                    Entenda como o motor Quantitativo Financeiro da API funciona por debaixo dos panos.
                </p>
            </div>

            <Card className="bg-slate-900 border-slate-800">
                <CardHeader>
                    <CardTitle className="text-xl text-cyan-400 flex items-center">
                        <Target className="w-5 h-5 mr-2" /> O Sistema de Notas (0 a 10)
                    </CardTitle>
                    <CardDescription className="text-slate-400">
                        A QFA (Quantitative Financial Analysis) agrega 5 pilares estruturais.
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4 text-sm leading-relaxed text-slate-300">
                    <p>
                        Cada empresa passa por um funil matemático onde seus indicadores são isolados, limpos e comparados com premissas macroeconômicas (como IPCA e Selic) e limites saudáveis teóricos. As 5 categorias são:
                    </p>
                    <ul className="list-disc leading-loose pl-5 space-y-2">
                        <li><strong>Solvência:</strong> Capacidade de não quebrar no curto prazo (Liquidez) e de pagar dívidas longas com caixa (Dívida L. / EBITDA).</li>
                        <li><strong>Eficiência:</strong> O quão bem a empresa transforma vendas em dinheiro puro no bolso (Margem Líquida e Margem EBITDA).</li>
                        <li><strong>Rentabilidade:</strong> Mede o retorno gerado para os acionistas (ROE) e o retorno contra o capital já investido (ROIC vs Selic).</li>
                        <li><strong>Crescimento:</strong> Histórico percentual de aumento de Vendas (Receita) e Lucros ano contra ano.</li>
                        <li><strong>Valuation:</strong> Preço sobre Lucro (P/L) e Preço sobre o Patrimônio (P/VP). Usa algoritmos adaptativos dependendo se a empresa é um Banco ou Indústria.</li>
                    </ul>
                </CardContent>
            </Card>

            <Card className="bg-slate-900 border-slate-800">
                <CardHeader>
                    <CardTitle className="text-xl text-rose-400 flex items-center">
                        <AlertTriangle className="w-5 h-5 mr-2" /> Contenção de Risco (Kill Switches)
                    </CardTitle>
                    <CardDescription className="text-slate-400">
                        Algoritmos forenses que derrubam as notas dinamicamente se encontrarem perigo.
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4 text-sm leading-relaxed text-slate-300">
                    <p>
                        Se a empresa parece atraente nos 5 pilares, mas exibe indícios matemáticos graves (conhecidos por Wall Street como fraudes contábeis ou falências iminentes), o QFA injeta os <em>Kill Switches</em>.
                    </p>
                    <div className="bg-slate-950 p-4 rounded border border-slate-800">
                        <h4 className="font-bold text-slate-200 mb-2">Altman Z-Score (Risco de Falência)</h4>
                        <p className="text-slate-400 mb-4">Se a equação de insolvência de Edward Altman cair abaixo da taxa segura, um alerta é emitido e todas as projeções da empresa de Ano 5 e Ano 10 são limitadas artificialmente à nota neutra de 5.0, impedindo o modelo de recomendar ações arriscadas só pelo "lucro alto temporário".</p>

                        <h4 className="font-bold text-slate-200 mb-2">Beneish M-Score (Manipulação Contábil)</h4>
                        <p className="text-slate-400">Um modelo probit que aponta as 8 distorções contábeis corporativas. Se a inflação nas receitas ou despesas de capital acionarem esse alerta, as métricas da empresa ganham o maior penalty do sistema, derrubando Global Score severamente.</p>
                    </div>
                </CardContent>
            </Card>

            <div className="flex justify-center mt-12">
                <Link to="/">
                    <Button variant="default" className="bg-slate-800 hover:bg-slate-700 text-slate-100">
                        Voltar para o Screener
                    </Button>
                </Link>
            </div>

        </div>
    );
}
