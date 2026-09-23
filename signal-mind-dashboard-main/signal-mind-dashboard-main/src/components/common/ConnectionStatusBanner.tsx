import React from 'react';
import { AlertCircle, Terminal, Play, RefreshCw, CheckCircle2 } from 'lucide-react';

interface ConnectionStatusBannerProps {
  isOnline: boolean;
  isSumoActive: boolean;
  error: string | null;
  onRefresh: () => void;
}

export const ConnectionStatusBanner: React.FC<ConnectionStatusBannerProps> = ({
  isOnline,
  isSumoActive,
  error,
  onRefresh,
}) => {
  if (isOnline && isSumoActive) {
    return null; // System is fully operational, no banner needed
  }

  return (
    <div className="mb-6 p-4 rounded-2xl border bg-slate-950/90 shadow-xl backdrop-blur-md transition-all animate-fade-in-up border-amber-500/40 bg-amber-950/10">
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-start space-x-3">
          <div className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 bg-amber-500/20 text-amber-400 border border-amber-500/40">
            <AlertCircle className="w-5 h-5" />
          </div>
          <div>
            <h4 className="text-sm font-bold text-slate-100 flex items-center gap-2">
              {!isOnline
                ? 'Backend Controller API Offline'
                : 'Awaiting Active SUMO Simulation Stream'}
            </h4>
            <p className="text-xs text-muted-foreground mt-0.5">
              {!isOnline
                ? 'Could not connect to Flask Controller API at http://127.0.0.1:5000. Start controller_api.py to enable real-time telemetry.'
                : 'Controller API is online. Start sumo_bridge.py or verify_multi_junction.py to stream live multi-junction TraCI simulation data.'}
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3 self-end md:self-auto">
          {/* Quick command reference */}
          <div className="hidden lg:flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-[11px] font-mono text-slate-300">
            <Terminal className="w-3.5 h-3.5 text-cyan-400" />
            <span>{!isOnline ? 'python sumo/controller_api.py' : 'python sumo/sumo_bridge.py --gui'}</span>
          </div>

          <button
            onClick={onRefresh}
            className="flex items-center space-x-1.5 px-3.5 py-1.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-md shadow-blue-500/20 transition-all"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Retry Connection</span>
          </button>
        </div>
      </div>
    </div>
  );
};
