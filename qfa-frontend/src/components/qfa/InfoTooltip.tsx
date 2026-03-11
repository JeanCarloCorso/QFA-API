import React from 'react';
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from "@/components/ui/tooltip";
import { Info } from "lucide-react";

interface InfoTooltipProps {
    content: string;
}

export function InfoTooltip({ content }: InfoTooltipProps) {
    return (
        <TooltipProvider delayDuration={200}>
            <Tooltip>
                <TooltipTrigger asChild>
                    <Info className="w-4 h-4 text-slate-400 hover:text-emerald-400 cursor-help transition-colors inline-block ml-1.5" />
                </TooltipTrigger>
                <TooltipContent className="max-w-xs bg-slate-900 text-slate-100 border-slate-700 shadow-xl leading-relaxed">
                    <p className="text-sm">{content}</p>
                </TooltipContent>
            </Tooltip>
        </TooltipProvider>
    );
}
