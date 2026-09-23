import React from 'react';
import { NetworkStatusResponse } from '../../api/types';
import { Car, Layers, Zap, AlertTriangle, ArrowUpRight, Clock } from 'lucide-react';

interface OverviewMetricsProps {
  data: NetworkStatusResponse | null;
  isOnline: boolean;
}

export const OverviewMetrics: React.FC<OverviewMetricsProps> = ({ data, isOnline }) => {
  if (!isOnline || !data) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="glass-card p-5 rounded-2xl border border-border/60 flex items-center justify-between opacity-60">
            <div>
              <div className="h-3.5 w-24 bg-muted rounded animate-pulse mb-2" />
              <div className="h-7 w-16 bg-muted rounded animate-pulse" />
            </div>
            <div className="w-10 h-10 rounded-xl bg-muted/40 animate-pulse" />
          </div>
        ))}
      </div>
    );
  }

  const junctions = data.junctions || {};
  const junctionIds = Object.keys(junctions);
  
  // Total Network Queue
  const totalN = data.counts?.N || 0;
  const totalE = data.counts?.E || 0;
  const totalS = data.counts?.S || 0;
  const totalW = data.counts?.W || 0;
  const totalQueue = totalN + totalE + totalS + totalW;

  // Average Queue per junction
  const activeCount = junctionIds.length || 1;
  const avgQueuePerJunction = (totalQueue / activeCount).toFixed(1);

  // Peak junction queue
  let maxQueue = 0;
  let busiestJunction = 'J1';
  junctionIds.forEach((id) => {
    const q = junctions[id]?.counts || { N: 0, E: 0, S: 0, W: 0 };
    const sum = q.N + q.E + q.S + q.W;
    if (sum > maxQueue) {
      maxQueue = sum;
      busiestJunction = id;
    }
  });

  const lastDec = data.last_decision || {};
  const lastPhase = lastDec.phase || '—';
  const lastGreen = lastDec.green || 0;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      {/* Total Network Queue */}
      <div className="glass-card p-5 rounded-2xl border border-blue-500/20 bg-gradient-to-br from-blue-950/20 via-slate-900/40 to-slate-950/60 relative overflow-hidden group hover:border-blue-500/40 transition-all">
        <div className="absolute top-0 right-0 w-24 h-24 bg-blue-500/5 rounded-full blur-2xl group-hover:bg-blue-500/10 transition-colors" />
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold text-slate-400 tracking-wider uppercase">
            Total Network Queue
          </span>
          <div className="w-8 h-8 rounded-lg bg-blue-500/10 border border-blue-500/30 flex items-center justify-center text-blue-400">
            <Car className="w-4 h-4" />
          </div>
        </div>
        <div className="flex items-baseline space-x-2">
          <span className="text-3xl font-extrabold font-mono text-white tracking-tight">
            {totalQueue}
          </span>
          <span className="text-xs text-blue-400/90 font-medium">vehicles queued</span>
        </div>
        <div className="mt-3 flex items-center space-x-3 text-[11px] font-mono text-slate-400 pt-2 border-t border-slate-800/80">
          <span>N: <strong className="text-slate-200">{totalN}</strong></span>
          <span>E: <strong className="text-slate-200">{totalE}</strong></span>
          <span>S: <strong className="text-slate-200">{totalS}</strong></span>
          <span>W: <strong className="text-slate-200">{totalW}</strong></span>
        </div>
      </div>

      {/* Active Intersections */}
      <div className="glass-card p-5 rounded-2xl border border-cyan-500/20 bg-gradient-to-br from-cyan-950/20 via-slate-900/40 to-slate-950/60 relative overflow-hidden group hover:border-cyan-500/40 transition-all">
        <div className="absolute top-0 right-0 w-24 h-24 bg-cyan-500/5 rounded-full blur-2xl group-hover:bg-cyan-500/10 transition-colors" />
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold text-slate-400 tracking-wider uppercase">
            Controlled Intersections
          </span>
          <div className="w-8 h-8 rounded-lg bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
            <Layers className="w-4 h-4" />
          </div>
        </div>
        <div className="flex items-baseline space-x-2">
          <span className="text-3xl font-extrabold font-mono text-white tracking-tight">
            {activeCount}
          </span>
          <span className="text-xs text-cyan-400 font-medium">J1 – J6 online</span>
        </div>
        <div className="mt-3 flex items-center justify-between text-[11px] font-mono text-slate-400 pt-2 border-t border-slate-800/80">
          <span>Avg Queue / Node:</span>
          <strong className="text-cyan-300 font-semibold">{avgQueuePerJunction} veh</strong>
        </div>
      </div>

      {/* Busiest Corridor */}
      <div className="glass-card p-5 rounded-2xl border border-amber-500/20 bg-gradient-to-br from-amber-950/20 via-slate-900/40 to-slate-950/60 relative overflow-hidden group hover:border-amber-500/40 transition-all">
        <div className="absolute top-0 right-0 w-24 h-24 bg-amber-500/5 rounded-full blur-2xl group-hover:bg-amber-500/10 transition-colors" />
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold text-slate-400 tracking-wider uppercase">
            Peak Congested Node
          </span>
          <div className="w-8 h-8 rounded-lg bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400">
            <AlertTriangle className="w-4 h-4" />
          </div>
        </div>
        <div className="flex items-baseline space-x-2">
          <span className="text-3xl font-extrabold font-mono text-amber-400 tracking-tight">
            {busiestJunction}
          </span>
          <span className="text-xs text-amber-300/80 font-medium">({maxQueue} queued)</span>
        </div>
        <div className="mt-3 flex items-center justify-between text-[11px] font-mono text-slate-400 pt-2 border-t border-slate-800/80">
          <span>Congestion Level:</span>
          <span className={`font-semibold ${maxQueue > 15 ? 'text-rose-400' : maxQueue > 8 ? 'text-amber-400' : 'text-emerald-400'}`}>
            {maxQueue > 15 ? 'HIGH DENSITY' : maxQueue > 8 ? 'MODERATE' : 'OPTIMAL'}
          </span>
        </div>
      </div>

      {/* Controller Decision Telemetry */}
      <div className="glass-card p-5 rounded-2xl border border-purple-500/20 bg-gradient-to-br from-purple-950/20 via-slate-900/40 to-slate-950/60 relative overflow-hidden group hover:border-purple-500/40 transition-all">
        <div className="absolute top-0 right-0 w-24 h-24 bg-purple-500/5 rounded-full blur-2xl group-hover:bg-purple-500/10 transition-colors" />
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold text-slate-400 tracking-wider uppercase">
            Latest Controller Action
          </span>
          <div className="w-8 h-8 rounded-lg bg-purple-500/10 border border-purple-500/30 flex items-center justify-center text-purple-400">
            <Zap className="w-4 h-4" />
          </div>
        </div>
        <div className="flex items-baseline space-x-2">
          <span className="text-3xl font-extrabold font-mono text-white tracking-tight">
            Phase {lastPhase}
          </span>
          <span className="text-xs text-purple-400 font-medium">for {lastGreen}s</span>
        </div>
        <div className="mt-3 flex items-center justify-between text-[11px] font-mono text-slate-400 pt-2 border-t border-slate-800/80">
          <span>Target Node:</span>
          <span className="text-purple-300 font-semibold">{lastDec.junction || 'Junction'}</span>
        </div>
      </div>
    </div>
  );
};
