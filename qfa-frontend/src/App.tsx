import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { ScreenerHome } from './pages/screener/ScreenerHome';
import { ActionDashboard } from './pages/dashboard/ActionDashboard';
import { Methodology } from './pages/methodology/Methodology';
import { AdminSync } from './pages/admin/AdminSync';
import { AdminService, type HealthResponse } from './services/api';
import { Activity, BookOpen, LineChart, Database } from 'lucide-react';

function HealthIndicator() {
  const [health, setHealth] = React.useState<HealthResponse | null>(null);

  React.useEffect(() => {
    async function checkHealth() {
      try {
        const data = await AdminService.getHealth();
        setHealth(data);
      } catch (err) {
        setHealth({ status: 'offline', dependencies: { database: 'error', yfinance: 'error' }, base_updated_percentage: 0 });
      }
    }
    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  if (!health) return null;

  const isHealthy = health.status === 'healthy';
  const isDegraded = health.status === 'degraded';

  return (
    <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-slate-900 border border-slate-800">
      <div className={`h-2 w-2 rounded-full ${isHealthy ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]' : isDegraded ? 'bg-amber-500' : 'bg-rose-500'}`} />
      <span className="text-[10px] font-bold uppercase tracking-widest text-slate-400">
        API: {health.status}
      </span>
    </div>
  );
}

function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-slate-950 font-sans antialiased text-slate-200">

      {/* GLOBAL NAVBAR */}
      <header className="sticky top-0 z-40 w-full border-b border-slate-800 bg-slate-950/80 backdrop-blur">
        <div className="container mx-auto flex h-16 max-w-7xl items-center justify-between px-4">
          <div className="flex items-center gap-8">
            <Link to="/" className="flex items-center gap-2 transition-colors hover:text-cyan-400">
              <Activity className="h-6 w-6 text-emerald-500" />
              <span className="font-bold text-lg tracking-tight">QFA Terminal</span>
            </Link>

            <nav className="hidden md:flex items-center gap-6">
              <Link to="/" className="flex items-center text-sm font-medium text-slate-400 hover:text-cyan-400 transition-colors">
                <LineChart className="h-4 w-4 mr-1.5" />
                Screener
              </Link>
              <Link to="/methodology" className="flex items-center text-sm font-medium text-slate-400 hover:text-cyan-400 transition-colors">
                <BookOpen className="h-4 w-4 mr-1.5" />
                Metodologia
              </Link>
              <Link to="/admin/sync" className="flex items-center text-sm font-medium text-slate-400 hover:text-cyan-400 transition-colors">
                <Database className="h-4 w-4 mr-1.5" />
                Admin/Sync
              </Link>
            </nav>
          </div>

          <HealthIndicator />
        </div>
      </header>

      {/* MAIN CONTENT AREA */}
      <main className="flex-1">
        {children}
      </main>

    </div>
  );
}

export default function App() {
  return (
    <Router>
      <AppLayout>
        <Routes>
          <Route path="/" element={<ScreenerHome />} />
          <Route path="/stock/:ticker" element={<ActionDashboard />} />
          <Route path="/methodology" element={<Methodology />} />
          <Route path="/admin/sync" element={<AdminSync />} />
        </Routes>
      </AppLayout>
    </Router>
  );
}
