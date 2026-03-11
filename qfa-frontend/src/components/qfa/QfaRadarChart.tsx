import React from 'react';
import {
    Radar,
    RadarChart as RechartsRadar,
    PolarGrid,
    PolarAngleAxis,
    PolarRadiusAxis,
    ResponsiveContainer,
    Tooltip
} from 'recharts';

interface RadarData {
    subject: string;
    A: number;
    fullMark: number;
}

interface QfaRadarProps {
    data: RadarData[];
    height?: number;
}

const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
        return (
            <div className="bg-slate-900 border border-slate-700 p-2 rounded shadow-xl text-xs">
                <p className="text-emerald-400 font-bold">{`${payload[0].payload.subject}`}</p>
                <p className="text-slate-200">{`Nota: ${payload[0].value.toFixed(1)} / 10`}</p>
            </div>
        );
    }
    return null;
};

export function QfaRadarChart({ data, height = 300 }: QfaRadarProps) {
    return (
        <div style={{ width: '100%', height: height }}>
            <ResponsiveContainer>
                <RechartsRadar cx="50%" cy="50%" outerRadius="70%" data={data}>
                    <PolarGrid stroke="#334155" />
                    <PolarAngleAxis dataKey="subject" tick={{ fill: '#94a3b8', fontSize: 12 }} />
                    <PolarRadiusAxis angle={30} domain={[0, 10]} tick={false} axisLine={false} />
                    <Radar
                        name="QFA Score"
                        dataKey="A"
                        stroke="#10b981"
                        fill="#10b981"
                        fillOpacity={0.4}
                        isAnimationActive={true}
                    />
                    <Tooltip content={<CustomTooltip />} />
                </RechartsRadar>
            </ResponsiveContainer>
        </div>
    );
}
