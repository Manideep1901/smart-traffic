import React from 'react';

interface TrafficLightVisualizerProps {
  phase: string;
  greenRemaining: number;
  direction: 'N' | 'E' | 'S' | 'W';
  compact?: boolean;
}

export const TrafficLightVisualizer: React.FC<TrafficLightVisualizerProps> = ({
  phase,
  greenRemaining,
  direction,
  compact = false,
}) => {
  // Determine if this direction's traffic movement is currently granted green
  // In SUMO 2x3 network:
  // Phase 'N' or 'S' serves North-South corridor
  // Phase 'E' or 'W' serves East-West corridor
  const isDirectGreen = phase === direction;
  const isCorridorGreen = 
    (direction === 'N' && (phase === 'N' || phase === 'S')) ||
    (direction === 'S' && (phase === 'N' || phase === 'S')) ||
    (direction === 'E' && (phase === 'E' || phase === 'W')) ||
    (direction === 'W' && (phase === 'E' || phase === 'W'));

  const isGreen = isCorridorGreen && greenRemaining > 2;
  const isYellow = isCorridorGreen && greenRemaining > 0 && greenRemaining <= 2;
  const isRed = !isCorridorGreen || greenRemaining <= 0;

  if (compact) {
    return (
      <div className="inline-flex items-center space-x-1.5 px-2 py-1 bg-slate-950/80 border border-slate-800 rounded-lg shadow-inner">
        <span className="text-[10px] font-mono font-bold text-slate-400 w-3 text-center">{direction}</span>
        <div className="flex space-x-1">
          <div className={`w-2.5 h-2.5 rounded-full transition-all duration-300 ${
            isRed 
              ? 'bg-rose-500 shadow-[0_0_8px_rgba(244,63,94,0.9)] ring-1 ring-rose-400' 
              : 'bg-rose-950/40 border border-rose-900/30'
          }`} />
          <div className={`w-2.5 h-2.5 rounded-full transition-all duration-300 ${
            isYellow 
              ? 'bg-amber-400 shadow-[0_0_8px_rgba(251,191,36,0.9)] ring-1 ring-amber-300 animate-pulse' 
              : 'bg-amber-950/40 border border-amber-900/30'
          }`} />
          <div className={`w-2.5 h-2.5 rounded-full transition-all duration-300 ${
            isGreen 
              ? 'bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.9)] ring-1 ring-emerald-300' 
              : 'bg-emerald-950/40 border border-emerald-900/30'
          }`} />
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center bg-slate-950/90 border border-slate-800 rounded-xl p-2 shadow-xl shadow-black/50">
      <div className="text-[11px] font-mono font-bold text-slate-300 mb-1.5 uppercase tracking-wider">
        Lane {direction}
      </div>
      <div className="flex flex-col space-y-1.5 bg-slate-900/90 p-1.5 rounded-lg border border-slate-800/80">
        {/* Red Light */}
        <div 
          className={`w-4 h-4 rounded-full transition-all duration-300 ${
            isRed 
              ? 'bg-rose-500 shadow-[0_0_12px_rgba(244,63,94,1)] ring-2 ring-rose-400' 
              : 'bg-rose-950/40 border border-rose-900/20'
          }`} 
          title="Stop (Red)"
        />
        {/* Yellow Light */}
        <div 
          className={`w-4 h-4 rounded-full transition-all duration-300 ${
            isYellow 
              ? 'bg-amber-400 shadow-[0_0_12px_rgba(251,191,36,1)] ring-2 ring-amber-300 animate-pulse' 
              : 'bg-amber-950/40 border border-amber-900/20'
          }`} 
          title="Prepare to Stop (Yellow)"
        />
        {/* Green Light */}
        <div 
          className={`w-4 h-4 rounded-full transition-all duration-300 ${
            isGreen 
              ? 'bg-emerald-400 shadow-[0_0_12px_rgba(52,211,153,1)] ring-2 ring-emerald-300' 
              : 'bg-emerald-950/40 border border-emerald-900/20'
          }`} 
          title="Proceed (Green)"
        />
      </div>
      <div className="mt-1.5 text-[10px] font-mono text-center">
        {isGreen ? (
          <span className="text-emerald-400 font-semibold">{greenRemaining}s</span>
        ) : isYellow ? (
          <span className="text-amber-400 font-semibold">{greenRemaining}s</span>
        ) : (
          <span className="text-slate-500">HOLD</span>
        )}
      </div>
    </div>
  );
};
