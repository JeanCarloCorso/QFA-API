import React from 'react';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import { Target, AlertTriangle, XOctagon } from 'lucide-react';

interface GlobalScoreBadgeProps {
    score: number;
    className?: string;
    size?: 'sm' | 'md' | 'lg';
}

export function getScoreColor(score: number): string {
    if (score >= 8.0) return 'bg-emerald-500 hover:bg-emerald-600 text-white';
    if (score >= 5.0) return 'bg-amber-500 hover:bg-amber-600 text-white';
    return 'bg-rose-500 hover:bg-rose-600 text-white';
}

export function getScoreIcon(score: number) {
    if (score >= 8.0) return <Target className="w-4 h-4 mr-1" />;
    if (score >= 5.0) return <AlertTriangle className="w-4 h-4 mr-1" />;
    return <XOctagon className="w-4 h-4 mr-1" />;
}

export function GlobalScoreBadge({ score, className, size = 'sm' }: GlobalScoreBadgeProps) {
    const colorClass = getScoreColor(score);

    const sizeClasses = {
        sm: 'text-xs px-2 py-0.5',
        md: 'text-sm px-3 py-1',
        lg: 'text-lg px-4 py-1.5'
    };

    return (
        <Badge
            variant="default"
            className={cn(
                colorClass,
                sizeClasses[size],
                'font-bold tracking-tight shadow-sm transition-all',
                className
            )}
        >
            {getScoreIcon(score)}
            {score.toFixed(2)} / 10
        </Badge>
    );
}
