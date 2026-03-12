import axios from 'axios';

// The QFA-API backend URL definition
export const API_BASE_URL = 'http://localhost:8000/api/v1';

export const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// --- TypeScript Definitions for QFA-API Responses ---

export interface MacroAssumptions {
    selic_used: number | null;
    ipca_used: number | null;
    pib_used: number | null;
}

export interface AnalysisMetadata {
    last_updated: string | null;
    macro_assumptions: MacroAssumptions;
}

export interface QfaScores {
    ano_1: number;
    ano_2: number;
    ano_5: number;
    ano_10: number;
}

export interface QfaFlags {
    bankruptcy_risk: boolean;
    manipulation_risk: boolean;
}

export interface QfaRawDataSummary {
    info: {
        sector: string;
        industry: string;
    };
    risk: { beta: number | null };
    growth: { revenue_growth: number | null; earnings_growth: number | null };
    solvency: { net_debt: number | null; current_ratio: number | null; net_debt_to_ebitda: number | null };
    cash_flow: { free_cash_flow_margin: number | null; operating_cash_flow_to_net_income: number | null };
    valuation: { price_to_book: number | null; warning?: string };
    efficiency: { warning?: string };
    projections: {
        min: number;
        max: number;
        mean: number;
        median: number;
        std: number;
    };
    profitability: { roe: number | null; roic: number | null };
    forensic_scores: {
        altman_z_score: number | null;
        bankruptcy_risk: boolean;
        beneish_m_score: number | null;
        manipulation_risk: boolean;
    };
}

export interface QfaAnalysis {
    error: string | null;
    status: string;
    ticker: string;
    global_score: number;
    scores: QfaScores;
    flags: QfaFlags;
    raw_data_summary: QfaRawDataSummary;
}

export interface StockEvaluationRecord {
    metadata: AnalysisMetadata;
    analysis: QfaAnalysis;
}

export interface ScreenerSectorResponse {
    warning: string | null;
    data: StockEvaluationRecord[];
}

export interface StressTestPayload {
    selic_esperada: number;
    ipca_esperado: number;
    pib_esperado: number;
}

export interface HealthResponse {
    status: string;
    dependencies: {
        database: string;
        yfinance: string;
    };
    base_updated_percentage: number;
}

export interface SyncCompaniesResponse {
    total_received_from_api: number;
    total_processed: number;
    message: string;
}

export interface TaskResponse {
    task_id: string;
    message: string;
}

// --- API Service Methods ---
export const ScreenerService = {
    getSectorRanking: async (sector: string, limit: number = 10): Promise<ScreenerSectorResponse> => {
        const encodedSector = encodeURIComponent(sector);
        const response = await api.get(`/screener/setor/${encodedSector}?limit=${limit}`);
        return response.data;
    },

    getTickerData: async (ticker: string): Promise<StockEvaluationRecord> => {
        const response = await api.get(`/screener/ticker/${ticker}`);
        return response.data;
    },

    getSectors: async (): Promise<string[]> => {
        const response = await api.get('/screener/sectors');
        return response.data;
    },

    syncScreener: async (payload: StressTestPayload): Promise<{ message: string }> => {
        const response = await api.post('/screener/sync', payload);
        return response.data;
    }
};

export const SandboxService = {
    runStressTest: async (ticker: string, payload: StressTestPayload): Promise<QfaAnalysis> => {
        const response = await api.post(`/sandbox/stress-test/${ticker}`, payload);
        return response.data;
    }
};

export const AdminService = {
    syncCompanies: async (): Promise<SyncCompaniesResponse> => {
        const response = await api.get('/companies/sync');
        return response.data;
    },
    getHealth: async (): Promise<HealthResponse> => {
        const response = await api.get('/health/');
        return response.data;
    }
};

export const AnalysisService = {
    startAnalysis: async (ticker: string, payload: StressTestPayload): Promise<TaskResponse> => {
        const response = await api.post(`/analysis/quant/${ticker}`, payload);
        return response.data;
    },
    getAnalysisResult: async (taskId: string): Promise<QfaAnalysis & { status: string }> => {
        const response = await api.get(`/analysis/result/${taskId}`);
        return response.data;
    }
};
