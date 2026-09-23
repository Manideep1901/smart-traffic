import React, { useState } from 'react';
import { JunctionInfo, JunctionCounts } from '../../api/types';
import { TrafficLightVisualizer } from '../signals/TrafficLightVisualizer';
import { trafficApi } from '../../api/trafficApi';
import { X, Clock, Zap, ArrowRight, ShieldCheck, RefreshCw } from 'lucide-react';

interface JunctionDetailModalProps {
  junctionId: string;
  info?: JunctionInfo;
  onClose: () => void;
  onRefresh: () => void;
}

export const JunctionDetailModal: React.FC<JunctionDetailModalProps> = ({
  junctionId,
  info,
  onClose,
  onRefresh,
}) => {
  const [isSimulating, setIsSimulating] = useState(false);
  const [manualMsg, setManualMsg] = useState<string | null>(null);

  const counts = info?.counts || { N: 0, E: 0, S: 0, W: 0 };
  const lastDec = info?.last_decision;
  const lastServed = info?.last_served || { N: 0, E: 0, S: 0, W: 0 };

  const phase = lastDec?.phase || 'N';
  const green = lastDec?.green || 0;
  const endTime = lastDec?.end_time || 0;
  const nowTs = Date.now() / 1000;
  const remaining = Math.max(0, Math.round(endTime - nowTs));

  const totalQueue = counts.N + counts.E + counts.S + counts.W;
  const directions: Array<'N' | 'E' | 'S' | 'W'> = ['N', 'E', 'S', 'W'];

  const handleRequestDecision = async () => {
    try {
      setIsSimulating(true);
      const res = await trafficApi.requestDecision(junctionId, counts);
      setManualMsg(`Decision computed: Phase ${res.phase} for ${res.green}s`);
      onRefresh();
    } catch (err: any) {
      setManualMsg(`Request failed: ${err.message}`);
    } finally {
      setIsSimulating(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fade-in-up">
      <div className="glass-card w-full max-w-2xl rounded-3xl p-6 border border-blue-500/40 bg-slate-950/95 shadow-2xl relative">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-5 right-5 p-2 rounded-xl bg-slate-900 border border-slate-700 text-slate-400 hover:text-white transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Header */}
        <div className="flex items-center space-x-3 mb-6 pb-4 border-b border-border/60">
          <div className="w-12 h-12 rounded-2xl bg-blue-600 text-white font-mono font-extrabold text-lg flex items-center justify-center shadow-lg shadow-blue-500/30">
            {junctionId}
          </div>
          <div>
            <h2 className="text-xl font-bold text-white tracking-tight">
              Intersection {junctionId} Detailed Telemetry
            </h2>
            <p className="text-xs text-muted-foreground font-mono">
              Signalized Multi-Junction Node • {totalQueue} Total Queued Vehicles
            </p>
          </div>
        </div>

        {/* Signal Status Bar */}
        <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 mb-6 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center space-x-3">
            <span className="w-3 h-3 rounded-full bg-emerald-400 animate-ping" />
            <div>
              <span className="text-xs text-slate-400">Current Active Green:</span>
              <div className="text-sm font-bold font-mono text-emerald-400">
                Direction {phase} ({green}s Total)
              </div>
            </div>
          </div>
          <div className="flex items-center space-x-2 font-mono text-xs text-slate-300">
            <Clock className="w-4 h-4 text-cyan-400" />
            <span>Remaining: <strong className="text-cyan-300 text-sm">{remaining}s</strong></span>
          </div>
        </div>

        {/* 4 Directions Signal Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
          {directions.map((d) => (
            <div key={d} className="bg-slate-900/60 p-3 rounded-2xl border border-slate-800/80 flex flex-col items-center">
              <TrafficLightVisualizer
                phase={phase}
                greenRemaining={remaining}
                direction={d}
                compact={false}
              />
              <div className="mt-3 w-full text-center text-xs font-mono pt-2 border-t border-slate-800">
                <div className="text-slate-400">Queue: <strong className="text-slate-200">{counts[d] || 0}</strong></div>
                <div className="text-slate-500 text-[10px]">Wait: {lastServed[d] || 0}s</div>
              </div>
            </div>
          ))}
        </div>

        {/* Manual Test Action */}
        <div className="pt-4 border-t border-border/60 flex items-center justify-between">
          <div className="text-xs text-slate-400 font-mono">
            {manualMsg ? <span className="text-cyan-400">{manualMsg}</span> : 'Request instant decision from controller API'}
          </div>
          <button
            onClick={handleRequestDecision}
            disabled={isSimulating}
            className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-lg shadow-blue-500/20 disabled:opacity-50 transition-all"
          >
            <Zap className="w-3.5 h-3.5" />
            <span>{isSimulating ? 'Querying API...' : 'Trigger Decision'}</span>
          </button>
        </div>
      </div>
    </div>
  );
};
