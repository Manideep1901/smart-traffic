import React from 'react';
import { Activity, Server, Radio, RefreshCw, Cpu, CheckCircle2, XCircle, Clock } from 'lucide-react';

interface TopHeaderProps {
  isOnline: boolean;
  isSumoActive: boolean;
  lastSyncTime: Date | null;
  pollingInterval: number;
  onPollingIntervalChange: (interval: number) => void;
  onRefresh: () => void;
  activeJunctionsCount: number;
}

export const TopHeader: React.FC<TopHeaderProps> = ({
  isOnline,
  isSumoActive,
  lastSyncTime,
  pollingInterval,
  onPollingIntervalChange,
  onRefresh,
  activeJunctionsCount,
}) => {
  return (
    <header className="border-b border-border/70 bg-card/60 backdrop-blur-md sticky top-0 z-50">
      <div className="max-w-[1920px] mx-auto px-4 lg:px-6 py-3 flex flex-wrap items-center justify-between gap-4">
        {/* Brand & System Title */}
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-600 via-indigo-600 to-cyan-500 flex items-center justify-center shadow-lg shadow-blue-500/20 border border-blue-400/30">
            <Radio className="w-5 h-5 text-white animate-pulse" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-xl font-bold tracking-tight bg-gradient-to-r from-white via-slate-100 to-slate-400 bg-clip-text text-transparent">
                SMART TRAFFIC CONTROL CENTER
              </h1>
              <span className="px-2 py-0.5 text-[10px] font-semibold tracking-wider uppercase rounded-full bg-blue-500/20 text-blue-300 border border-blue-400/30">
                SUMO Multi-Junction
              </span>
            </div>
            <p className="text-xs text-muted-foreground flex items-center gap-2">
              <span>Intelligent Signal Control</span>
              <span>•</span>
              <span className="font-mono text-[11px] text-cyan-400/90">2x3 Grid Topology (J1–J6)</span>
            </p>
          </div>
        </div>

        {/* Live System Status Badges */}
        <div className="flex items-center flex-wrap gap-2.5">
          {/* API Backend Health */}
          <div className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg border text-xs font-medium transition-colors ${
            isOnline 
              ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' 
              : 'bg-rose-500/10 text-rose-400 border-rose-500/30'
          }`}>
            <Server className="w-3.5 h-3.5" />
            <span>API {isOnline ? 'CONNECTED (:5000)' : 'DISCONNECTED'}</span>
            {isOnline ? (
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
            ) : (
              <XCircle className="w-3.5 h-3.5 text-rose-400" />
            )}
          </div>

          {/* SUMO TraCI Status */}
          <div className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg border text-xs font-medium transition-colors ${
            isSumoActive 
              ? 'bg-cyan-500/10 text-cyan-300 border-cyan-500/30' 
              : 'bg-amber-500/10 text-amber-400 border-amber-500/30'
          }`}>
            <Activity className="w-3.5 h-3.5" />
            <span>SUMO SIMULATION {isSumoActive ? `ACTIVE (${activeJunctionsCount} TLS)` : 'WAITING'}</span>
            {isSumoActive && (
              <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
            )}
          </div>

          {/* Controller Mode */}
          <div className="flex items-center space-x-2 px-3 py-1.5 rounded-lg border bg-purple-500/10 text-purple-300 border-purple-500/30 text-xs font-medium">
            <Cpu className="w-3.5 h-3.5" />
            <span>ADAPTIVE RL/HEURISTIC</span>
          </div>

          {/* Polling Interval Selector */}
          <div className="flex items-center space-x-1.5 bg-secondary/40 border border-border/80 rounded-lg p-1 text-xs">
            <span className="text-muted-foreground px-1.5 flex items-center gap-1">
              <Clock className="w-3 h-3" /> Sync:
            </span>
            {[500, 1000, 2000].map((ms) => (
              <button
                key={ms}
                onClick={() => onPollingIntervalChange(ms)}
                className={`px-2 py-0.5 rounded text-[11px] font-mono transition-all ${
                  pollingInterval === ms
                    ? 'bg-primary text-primary-foreground font-semibold shadow-sm'
                    : 'text-muted-foreground hover:text-foreground hover:bg-secondary'
                }`}
              >
                {ms / 1000}s
              </button>
            ))}
          </div>

          {/* Manual Refresh Button */}
          <button
            onClick={onRefresh}
            className="p-1.5 rounded-lg border border-border/80 bg-secondary/30 hover:bg-secondary text-muted-foreground hover:text-foreground transition-all"
            title="Force Refresh"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>
    </header>
  );
};
