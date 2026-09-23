import React from 'react';
import { NetworkStatusResponse } from '../../api/types';
import { Cpu, Zap, ShieldCheck, Settings, CheckCircle } from 'lucide-react';

interface RLControllerPanelProps {
  data: NetworkStatusResponse | null;
}

export const RLControllerPanel: React.FC<RLControllerPanelProps> = ({ data }) => {
  const lastDec = data?.last_decision || {};

  return (
    <div className="glass-card rounded-2xl p-5 border border-border/70 bg-slate-950/80">
      <div className="flex items-center justify-between mb-4 pb-3 border-b border-border/60">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-lg bg-purple-500/10 border border-purple-500/30 flex items-center justify-center text-purple-400">
            <Cpu className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-100 tracking-wide uppercase">
              Intelligent Controller Telemetry
            </h3>
            <p className="text-[11px] text-muted-foreground">
              Deep Reinforcement Learning (DQN) & Multi-Agent Priority Optimization
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-purple-500/20 text-purple-300 border border-purple-500/40">
            ACTIVE AGENT
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Model Architecture & Weights */}
        <div className="bg-slate-900/60 p-3.5 rounded-xl border border-slate-800/80">
          <div className="flex items-center space-x-2 text-xs font-semibold text-slate-300 mb-2">
            <Settings className="w-3.5 h-3.5 text-purple-400" />
            <span>Priority Heuristic Weights</span>
          </div>
          <div className="space-y-1.5 text-xs font-mono">
            <div className="flex justify-between text-slate-400">
              <span>Queue Weight (α):</span>
              <span className="text-slate-200 font-bold">1.0</span>
            </div>
            <div className="flex justify-between text-slate-400">
              <span>Wait Time Weight (β):</span>
              <span className="text-slate-200 font-bold">0.6</span>
            </div>
            <div className="flex justify-between text-slate-400">
              <span>Saturation Flow (S):</span>
              <span className="text-slate-200 font-bold">1.8 s/veh</span>
            </div>
            <div className="flex justify-between text-slate-400">
              <span>Green Bounds:</span>
              <span className="text-slate-200 font-bold">6s – 45s</span>
            </div>
          </div>
        </div>

        {/* Anti-Starvation Guard */}
        <div className="bg-slate-900/60 p-3.5 rounded-xl border border-slate-800/80">
          <div className="flex items-center space-x-2 text-xs font-semibold text-slate-300 mb-2">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            <span>Anti-Starvation Rotation</span>
          </div>
          <p className="text-[11px] text-slate-400 leading-relaxed">
            The controller monitors consecutive phase serves. When a single direction is served &gt;2 consecutive cycles, the rotation guard forces phase transition to prevent starvation on lower-volume cross streets.
          </p>
          <div className="mt-2 text-[10px] font-mono text-emerald-400 flex items-center space-x-1">
            <CheckCircle className="w-3 h-3" />
            <span>Guard Status: ENFORCED (Max Repeat = 2)</span>
          </div>
        </div>

        {/* Latest Controller Decision */}
        <div className="bg-slate-900/60 p-3.5 rounded-xl border border-slate-800/80">
          <div className="flex items-center space-x-2 text-xs font-semibold text-slate-300 mb-2">
            <Zap className="w-3.5 h-3.5 text-cyan-400" />
            <span>Active Decision Snapshot</span>
          </div>
          <div className="space-y-1.5 text-xs font-mono">
            <div className="flex justify-between text-slate-400">
              <span>Target Junction:</span>
              <span className="text-cyan-300 font-bold">{lastDec.junction || 'Junction'}</span>
            </div>
            <div className="flex justify-between text-slate-400">
              <span>Chosen Phase:</span>
              <span className="text-emerald-400 font-bold">Direction {lastDec.phase || '—'}</span>
            </div>
            <div className="flex justify-between text-slate-400">
              <span>Green Allocated:</span>
              <span className="text-cyan-300 font-bold">{lastDec.green || 0} seconds</span>
            </div>
            <div className="flex justify-between text-slate-400">
              <span>Safety Clearance:</span>
              <span className="text-amber-300 font-bold">1.0s All-Red Gap</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
