import React, { useState } from 'react';
import { NetworkStatusResponse } from '../../api/types';
import { Layers, Compass, ZoomIn, ZoomOut, Maximize2 } from 'lucide-react';

interface NetworkMapViewProps {
  data: NetworkStatusResponse | null;
  selectedJunctionId: string;
  onSelectJunction: (id: string) => void;
}

export const NetworkMapView: React.FC<NetworkMapViewProps> = ({
  data,
  selectedJunctionId,
  onSelectJunction,
}) => {
  const [zoom, setZoom] = useState<number>(1);

  // SUMO Coordinates to SVG ViewBox Mapping
  // SUMO: X from -350 to 2150 (width 2500), Y from -300 to 1000 (height 1300)
  // In SUMO, Y goes UP. In SVG, Y goes DOWN.
  const svgWidth = 1000;
  const svgHeight = 520;

  const toSvgX = (x: number) => ((x + 350) / 2500) * (svgWidth - 100) + 50;
  const toSvgY = (y: number) => svgHeight - (((y + 300) / 1300) * (svgHeight - 80) + 40);

  // Node coordinate definitions matching multi_junction.nod.xml
  const nodes = {
    // 6 Signalized Intersections
    J1: { x: toSvgX(400), y: toSvgY(500), name: 'J1', type: 'tls', desc: 'Central West Corridor' },
    J2: { x: toSvgX(950), y: toSvgY(500), name: 'J2', type: 'tls', desc: 'Central Plaza Hub' },
    J3: { x: toSvgX(1600), y: toSvgY(500), name: 'J3', type: 'tls', desc: 'Highway Interchange' },
    J4: { x: toSvgX(250), y: toSvgY(150), name: 'J4', type: 'tls', desc: 'Southwest District' },
    J5: { x: toSvgX(900), y: toSvgY(150), name: 'J5', type: 'tls', desc: 'South Central Avenue' },
    J6: { x: toSvgX(1600), y: toSvgY(150), name: 'J6', type: 'tls', desc: 'Southeast Express Node' },

    // 10 Perimeter Entry/Exit Nodes
    W1: { x: toSvgX(-300), y: toSvgY(500), name: 'W1', type: 'perimeter', desc: 'West Highway Entry' },
    W2: { x: toSvgX(-300), y: toSvgY(150), name: 'W2', type: 'perimeter', desc: 'West Local Entry' },
    E1: { x: toSvgX(2100), y: toSvgY(500), name: 'E1', type: 'perimeter', desc: 'East Highway Exit' },
    E2: { x: toSvgX(2100), y: toSvgY(150), name: 'E2', type: 'perimeter', desc: 'East Local Exit' },
    N1: { x: toSvgX(50), y: toSvgY(850), name: 'N1', type: 'perimeter', desc: 'Northwest Diagonal' },
    N2: { x: toSvgX(950), y: toSvgY(950), name: 'N2', type: 'perimeter', desc: 'North Arterial Feeder' },
    N3: { x: toSvgX(1600), y: toSvgY(950), name: 'N3', type: 'perimeter', desc: 'North Highway Terminal' },
    S1: { x: toSvgX(250), y: toSvgY(-250), name: 'S1', type: 'perimeter', desc: 'South District Gate' },
    S2: { x: toSvgX(900), y: toSvgY(-250), name: 'S2', type: 'perimeter', desc: 'South Connector Gate' },
    S3: { x: toSvgX(1600), y: toSvgY(-250), name: 'S3', type: 'perimeter', desc: 'South Highway Terminal' },
  };

  const junctionsData = data?.junctions || {};

  return (
    <div className="glass-card rounded-2xl border border-border/70 overflow-hidden relative flex flex-col bg-slate-950/80">
      {/* Map Control Bar */}
      <div className="px-5 py-3.5 border-b border-border/60 bg-slate-900/60 flex items-center justify-between">
        <div className="flex items-center space-x-2.5">
          <div className="w-2.5 h-2.5 rounded-full bg-blue-500 animate-pulse" />
          <span className="text-sm font-bold text-slate-200 tracking-wide uppercase">
            Multi-Junction Topology View (SUMO Network)
          </span>
          <span className="text-xs text-muted-foreground font-mono">
            • 6 Signalized Intersections • 10 Perimeter Nodes • 22 Flows
          </span>
        </div>

        {/* Legend & Controls */}
        <div className="flex items-center space-x-3 text-xs">
          <div className="flex items-center space-x-1.5 text-slate-400">
            <span className="w-4 h-1.5 bg-blue-500 rounded-full inline-block" />
            <span>3-Lane Highway</span>
          </div>
          <div className="flex items-center space-x-1.5 text-slate-400">
            <span className="w-4 h-1.5 bg-slate-600 rounded-full inline-block" />
            <span>2-Lane Local</span>
          </div>
          <div className="flex items-center space-x-1.5 text-slate-400">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 shadow-[0_0_6px_rgba(52,211,153,0.8)] inline-block" />
            <span>Green Phase</span>
          </div>
          <div className="flex items-center space-x-1.5 text-slate-400">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-500 shadow-[0_0_6px_rgba(244,63,94,0.8)] inline-block" />
            <span>Red Phase</span>
          </div>

          <div className="flex items-center space-x-1 border border-border/70 rounded-lg p-0.5 bg-slate-900">
            <button
              onClick={() => setZoom((z) => Math.min(z + 0.1, 1.4))}
              className="p-1 hover:bg-slate-800 rounded text-slate-300"
              title="Zoom In"
            >
              <ZoomIn className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={() => setZoom((z) => Math.max(z - 0.1, 0.8))}
              className="p-1 hover:bg-slate-800 rounded text-slate-300"
              title="Zoom Out"
            >
              <ZoomOut className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={() => setZoom(1)}
              className="p-1 hover:bg-slate-800 rounded text-slate-300"
              title="Reset Zoom"
            >
              <Maximize2 className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>

      {/* SVG Canvas */}
      <div className="relative w-full h-[480px] bg-gradient-to-b from-slate-950 via-slate-900/90 to-slate-950 overflow-hidden flex items-center justify-center select-none">
        {/* Subtle grid background */}
        <div 
          className="absolute inset-0 opacity-15 pointer-events-none" 
          style={{
            backgroundImage: `radial-gradient(circle, rgba(148, 163, 184, 0.25) 1px, transparent 1px)`,
            backgroundSize: '24px 24px'
          }}
        />

        <svg
          viewBox={`0 0 ${svgWidth} ${svgHeight}`}
          className="w-full h-full max-h-[480px] transition-transform duration-300"
          style={{ transform: `scale(${zoom})` }}
        >
          {/* Definitions for gradients and markers */}
          <defs>
            <linearGradient id="hwyGrad" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#1e3a8a" stopOpacity="0.8" />
              <stop offset="50%" stopColor="#3b82f6" stopOpacity="0.9" />
              <stop offset="100%" stopColor="#1e3a8a" stopOpacity="0.8" />
            </linearGradient>
            <linearGradient id="vHwyGrad" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#1e3a8a" stopOpacity="0.8" />
              <stop offset="50%" stopColor="#3b82f6" stopOpacity="0.9" />
              <stop offset="100%" stopColor="#1e3a8a" stopOpacity="0.8" />
            </linearGradient>
            <filter id="glowGreen" x="-20%" y="-20%" width="140%" height="140%">
              <feDropShadow dx="0" dy="0" stdDeviation="4" floodColor="#10b981" floodOpacity="0.9" />
            </filter>
            <filter id="glowRed" x="-20%" y="-20%" width="140%" height="140%">
              <feDropShadow dx="0" dy="0" stdDeviation="4" floodColor="#f43f5e" floodOpacity="0.8" />
            </filter>
          </defs>

          {/* ======================================================== */}
          {/* ROADS & HIGHWAYS LAYER                                   */}
          {/* ======================================================== */}

          {/* 1. Central Horizontal Highway: W1 -> J1 -> J2 -> J3 -> E1 (3 Lanes each way) */}
          <line
            x1={nodes.W1.x} y1={nodes.W1.y}
            x2={nodes.E1.x} y2={nodes.E1.y}
            stroke="#1e293b" strokeWidth="22" strokeLinecap="round"
          />
          <line
            x1={nodes.W1.x} y1={nodes.W1.y}
            x2={nodes.E1.x} y2={nodes.E1.y}
            stroke="url(#hwyGrad)" strokeWidth="16" strokeLinecap="round"
          />
          <line
            x1={nodes.W1.x} y1={nodes.W1.y}
            x2={nodes.E1.x} y2={nodes.E1.y}
            stroke="#f8fafc" strokeWidth="1.5" strokeDasharray="6 8" opacity="0.6"
          />

          {/* 2. Right Vertical Highway: N3 -> J3 -> J6 -> S3 (3 Lanes each way) */}
          <line
            x1={nodes.N3.x} y1={nodes.N3.y}
            x2={nodes.S3.x} y2={nodes.S3.y}
            stroke="#1e293b" strokeWidth="22" strokeLinecap="round"
          />
          <line
            x1={nodes.N3.x} y1={nodes.N3.y}
            x2={nodes.S3.x} y2={nodes.S3.y}
            stroke="url(#vHwyGrad)" strokeWidth="16" strokeLinecap="round"
          />
          <line
            x1={nodes.N3.x} y1={nodes.N3.y}
            x2={nodes.S3.x} y2={nodes.S3.y}
            stroke="#f8fafc" strokeWidth="1.5" strokeDasharray="6 8" opacity="0.6"
          />

          {/* 3. Southern Local Arterial: W2 -> J4 -> J5 -> J6 -> E2 (2 Lanes each way) */}
          <line
            x1={nodes.W2.x} y1={nodes.W2.y}
            x2={nodes.E2.x} y2={nodes.E2.y}
            stroke="#1e293b" strokeWidth="16" strokeLinecap="round"
          />
          <line
            x1={nodes.W2.x} y1={nodes.W2.y}
            x2={nodes.E2.x} y2={nodes.E2.y}
            stroke="#334155" strokeWidth="10" strokeLinecap="round"
          />
          <line
            x1={nodes.W2.x} y1={nodes.W2.y}
            x2={nodes.E2.x} y2={nodes.E2.y}
            stroke="#94a3b8" strokeWidth="1" strokeDasharray="4 6" opacity="0.5"
          />

          {/* 4. Diagonal Road: N1 -> J1 (2 Lanes each way) */}
          <line
            x1={nodes.N1.x} y1={nodes.N1.y}
            x2={nodes.J1.x} y2={nodes.J1.y}
            stroke="#1e293b" strokeWidth="16" strokeLinecap="round"
          />
          <line
            x1={nodes.N1.x} y1={nodes.N1.y}
            x2={nodes.J1.x} y2={nodes.J1.y}
            stroke="#475569" strokeWidth="10" strokeLinecap="round"
          />
          <line
            x1={nodes.N1.x} y1={nodes.N1.y}
            x2={nodes.J1.x} y2={nodes.J1.y}
            stroke="#cbd5e1" strokeWidth="1" strokeDasharray="4 6" opacity="0.5"
          />

          {/* 5. Vertical Connectors: J1 -> J4 -> S1 */}
          <line
            x1={nodes.J1.x} y1={nodes.J1.y}
            x2={nodes.S1.x} y2={nodes.S1.y}
            stroke="#1e293b" strokeWidth="14" strokeLinecap="round"
          />
          <line
            x1={nodes.J1.x} y1={nodes.J1.y}
            x2={nodes.S1.x} y2={nodes.S1.y}
            stroke="#334155" strokeWidth="8" strokeLinecap="round"
          />

          {/* 6. Vertical Connectors: N2 -> J2 -> J5 -> S2 */}
          <line
            x1={nodes.N2.x} y1={nodes.N2.y}
            x2={nodes.S2.x} y2={nodes.S2.y}
            stroke="#1e293b" strokeWidth="14" strokeLinecap="round"
          />
          <line
            x1={nodes.N2.x} y1={nodes.N2.y}
            x2={nodes.S2.x} y2={nodes.S2.y}
            stroke="#334155" strokeWidth="8" strokeLinecap="round"
          />

          {/* ======================================================== */}
          {/* PERIMETER BOUNDARY NODES (N1..N3, S1..S3, W1..W2, E1..E2)*/}
          {/* ======================================================== */}
          {Object.entries(nodes)
            .filter(([_, n]) => n.type === 'perimeter')
            .map(([id, n]) => (
              <g key={id} className="cursor-default">
                <circle cx={n.x} cy={n.y} r="8" fill="#0f172a" stroke="#64748b" strokeWidth="2" />
                <circle cx={n.x} cy={n.y} r="3" fill="#94a3b8" />
                <text
                  x={n.x}
                  y={n.y - 12}
                  textAnchor="middle"
                  fill="#94a3b8"
                  fontSize="10"
                  fontFamily="monospace"
                  fontWeight="bold"
                >
                  {id}
                </text>
              </g>
            ))}

          {/* ======================================================== */}
          {/* SIGNALIZED JUNCTION NODES (J1 to J6)                      */}
          {/* ======================================================== */}
          {(['J1', 'J2', 'J3', 'J4', 'J5', 'J6'] as const).map((id) => {
            const node = nodes[id];
            const jInfo = junctionsData[id];
            const counts = jInfo?.counts || { N: 0, E: 0, S: 0, W: 0 };
            const qSum = counts.N + counts.E + counts.S + counts.W;
            const lastDec = jInfo?.last_decision;
            const phase = lastDec?.phase || 'N';
            const green = lastDec?.green || 0;
            const isSelected = selectedJunctionId === id;

            // Determine active green direction
            const isNSGreen = phase === 'N' || phase === 'S';
            const isEWGreen = phase === 'E' || phase === 'W';

            return (
              <g
                key={id}
                onClick={() => onSelectJunction(id)}
                className="cursor-pointer transition-all duration-200"
                style={{ filter: isSelected ? 'drop-shadow(0 0 12px rgba(59, 130, 246, 0.9))' : undefined }}
              >
                {/* Node Outer Glow & Pulse on Selection */}
                {isSelected && (
                  <circle cx={node.x} cy={node.y} r="38" fill="none" stroke="#3b82f6" strokeWidth="2" strokeDasharray="4 4" className="animate-spin" />
                )}

                {/* Main Junction Base Circle */}
                <circle
                  cx={node.x}
                  cy={node.y}
                  r="28"
                  fill="#090d16"
                  stroke={isSelected ? '#60a5fa' : qSum > 12 ? '#f43f5e' : qSum > 6 ? '#fbbf24' : '#334155'}
                  strokeWidth={isSelected ? '3' : '2'}
                />

                {/* Dynamic Traffic Signal State Halos on Junction Approaches */}
                {/* North Indicator */}
                <circle
                  cx={node.x}
                  cy={node.y - 18}
                  r="4.5"
                  fill={isNSGreen ? '#10b981' : '#f43f5e'}
                  filter={isNSGreen ? 'url(#glowGreen)' : 'url(#glowRed)'}
                />
                {/* South Indicator */}
                <circle
                  cx={node.x}
                  cy={node.y + 18}
                  r="4.5"
                  fill={isNSGreen ? '#10b981' : '#f43f5e'}
                  filter={isNSGreen ? 'url(#glowGreen)' : 'url(#glowRed)'}
                />
                {/* East Indicator */}
                <circle
                  cx={node.x + 18}
                  cy={node.y}
                  r="4.5"
                  fill={isEWGreen ? '#10b981' : '#f43f5e'}
                  filter={isEWGreen ? 'url(#glowGreen)' : 'url(#glowRed)'}
                />
                {/* West Indicator */}
                <circle
                  cx={node.x - 18}
                  cy={node.y}
                  r="4.5"
                  fill={isEWGreen ? '#10b981' : '#f43f5e'}
                  filter={isEWGreen ? 'url(#glowGreen)' : 'url(#glowRed)'}
                />

                {/* Junction Label & Queue Count */}
                <text
                  x={node.x}
                  y={node.y - 1}
                  textAnchor="middle"
                  fill="#ffffff"
                  fontSize="13"
                  fontWeight="bold"
                  fontFamily="sans-serif"
                >
                  {id}
                </text>
                <text
                  x={node.x}
                  y={node.y + 11}
                  textAnchor="middle"
                  fill={qSum > 10 ? '#fb7185' : '#38bdf8'}
                  fontSize="9"
                  fontFamily="monospace"
                  fontWeight="bold"
                >
                  {qSum} veh
                </text>

                {/* Active Phase Badge / Callout */}
                <g transform={`translate(${node.x - 22}, ${node.y - 44})`}>
                  <rect
                    width="44"
                    height="16"
                    rx="4"
                    fill="#020617"
                    stroke={isNSGreen ? '#059669' : '#2563eb'}
                    strokeWidth="1"
                  />
                  <text
                    x="22"
                    y="11.5"
                    textAnchor="middle"
                    fill={isNSGreen ? '#34d399' : '#60a5fa'}
                    fontSize="9"
                    fontFamily="monospace"
                    fontWeight="bold"
                  >
                    {phase} • {green}s
                  </text>
                </g>
              </g>
            );
          })}
        </svg>

        {/* Compass Rose Overlay */}
        <div className="absolute top-4 right-4 p-2 rounded-xl bg-slate-950/80 border border-border/60 shadow-lg text-slate-400 flex flex-col items-center pointer-events-none">
          <Compass className="w-5 h-5 text-blue-400 mb-1" />
          <div className="text-[10px] font-mono font-bold leading-tight flex flex-col items-center">
            <span className="text-blue-300">N</span>
            <div className="flex space-x-2">
              <span>W</span>
              <span>E</span>
            </div>
            <span>S</span>
          </div>
        </div>
      </div>
    </div>
  );
};
