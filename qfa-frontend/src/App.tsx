import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { ScreenerHome } from './pages/screener/ScreenerHome';
import { ActionDashboard } from './pages/dashboard/ActionDashboard';
import { Methodology } from './pages/methodology/Methodology';
import { Activity, BookOpen, LineChart } from 'lucide-react';

function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-slate-950 font-sans antialiased text-slate-200">

      {/* GLOBAL NAVBAR */}
      <header className="sticky top-0 z-40 w-full border-b border-slate-800 bg-slate-950/80 backdrop-blur">
        <div className="container mx-auto flex h-16 max-w-7xl items-center justify-between px-4">
          <Link to="/" className="flex items-center gap-2 transition-colors hover:text-cyan-400">
            <Activity className="h-6 w-6 text-emerald-500" />
            <span className="font-bold text-lg tracking-tight">QFA Terminal</span>
          </Link>

          <nav className="flex items-center gap-6">
            <Link to="/" className="flex items-center text-sm font-medium text-slate-400 hover:text-cyan-400 transition-colors">
              <LineChart className="h-4 w-4 mr-1.5" />
              Screener
            </Link>
            <Link to="/methodology" className="flex items-center text-sm font-medium text-slate-400 hover:text-cyan-400 transition-colors">
              <BookOpen className="h-4 w-4 mr-1.5" />
              Metodologia
            </Link>
          </nav>
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
        </Routes>
      </AppLayout>
    </Router>
  );
}
