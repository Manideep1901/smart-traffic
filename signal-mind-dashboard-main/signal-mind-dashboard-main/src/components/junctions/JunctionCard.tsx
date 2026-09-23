import React from 'react';
import { JunctionInfo } from '../../api/types';
import { TrafficLightVisualizer } from '../signals/TrafficLightVisualizer';
import { Radio, ArrowRight, Clock, ShieldAlert } from 'lucide-react';

interface JunctionCardProps {
  id: string;
  name: string;
  roadType: string;
  info?: JunctionInfo;
  isSelected: boolean;
  onSelect: (id: string) => void;
}

export const JunctionCard: React.FC<JunctionCardProps> = ({
  id,
  name,
  roadType,
  info,
  isSelected,
  onSelect,
}) => {
  const counts = info?.counts || { N: 0, E: 0, S: 0, W: 0 };
  const lastDec = info?.last_decision;
  const lastServed = info?.last_served || { N: 0, E: 0, S: 0, W: 0 };

  const phase = lastDec?.phase || 'N';
  const green = lastDec?.green || 0;
  const endTime = lastDec?.end_time || 0;
  const nowTs = Date.now() / 1000;
  const remaining = Math.max(0, Math.round(endTime - nowTs));

  const totalQueue = counts.N + counts.E + counts.S + counts.W;
  const maxQueueLane = Math.max(counts.N, counts.E, counts.S, counts.W);

  // Road directions
  const directions: Array<'N' | 'E' | 'S' | 'W'> = ['N', 'E', 'S', 'W'];

  return (
    <div
      onClick={() => onSelect(id)}
      className={`glass-card rounded-2xl p-4 transition-all duration-300 cursor-pointer border ${
        isSelected
          ? 'border-blue-500 bg-blue-950/20 shadow-[0_0_20px_rgba(59,130,246,0.3)] ring-1 ring-blue-400/50'
          : 'border-border/60 hover:border-slate-600 bg-slate-900/40 hover:bg-slate-900/60'
      }`}
    >
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-border/50">
        <div className="flex items-center space-x-2.5">
          <div className={`w-8 h-8 rounded-lg flex items-center justify-center font-bold font-mono text-sm shadow-md ${
            isSelected 
              ? 'bg-blue-600 text-white' 
              : 'bg-slate-800 text-slate-200 border border-slate-700'
          }`}>
            {id}
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-100 tracking-wide">{name}</h3>
            <p className="text-[11px] text-muted-foreground">{roadType}</p>
          </div>
        </div>

        {/* Total Queue Badge */}
        <div className="text-right">
          <span className={`px-2 py-0.5 rounded-full text-xs font-mono font-bold ${
            totalQueue > 12 
              ? 'bg-rose-500/20 text-rose-400 border border-rose-500/40' 
              : totalQueue > 6 
              ? 'bg-amber-500/20 text-amber-400 border border-amber-500/40' 
              : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
          }`}>
            {totalQueue} Queued
          </span>
        </div>
      </div>

      {/* Active Phase & Signal Banner */}
      <div className="my-3 px-3 py-2 rounded-xl bg-slate-950/60 border border-slate-800/80 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
          <span className="text-xs font-mono font-medium text-slate-300">
            Phase <strong className="text-emerald-400">{phase}</strong> Green
          </span>
        </div>
        <div className="flex items-center space-x-1.5 font-mono text-xs text-slate-400">
          <Clock className="w-3 h-3 text-cyan-400" />
          <span>{remaining}s remaining</span>
          <span className="text-slate-600">({green}s total)</span>
        </div>
      </div>

      {/* 4 Approach Queue Bars */}
      <div className="space-y-2 my-3">
        {directions.map((d) => {
          const q = counts[d] || 0;
          const waitTime = lastServed[d] || 0;
          const isGreenLane = phase === d;
          const percent = Math.min(100, Math.round((q / (maxQueueLane || 1)) * 100));

          return (
            <div key={d} className="flex items-center text-xs">
              <span className="w-5 font-mono font-bold text-slate-400">{d}</span>
              <div className="flex-1 mx-2 h-2 bg-slate-950 rounded-full overflow-hidden border border-slate-800/60">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${
                    isGreenLane
                      ? 'bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)]'
                      : q > 6
                      ? 'bg-rose-500'
                      : 'bg-blue-500'
                  }`}
                  style={{ width: `${percent > 0 ? Math.max(percent, 8) : 0}%` }}
                />
              </div>
              <span className="w-8 font-mono font-semibold text-right text-slate-200">
                {q} <span className="text-[10px] text-slate-500 font-normal">v</span>
              </span>
              <span className="w-12 text-[10px] font-mono text-right text-slate-400">
                {waitTime}s w
              </span>
            </div>
          );
        })}
      </div>

      {/* Traffic Light Visualizers (Mini row) */}
      <div className="pt-2 border-t border-border/40 flex items-center justify-between">
        <span className="text-[10px] text-slate-500 font-mono">Signals (N/E/S/W):</span>
        <div className="flex space-x-1">
          {directions.map((d) => (
            <TrafficLightVisualizer
              key={d}
              phase={phase}
              greenRemaining={remaining}
              direction={d}
              compact={true}
            />
          ))}
        </div>
      </div>
    </div>
  );
};
