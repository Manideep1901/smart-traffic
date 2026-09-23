import React from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
} from 'recharts';
import { HistoricalPoint } from '../../api/types';
import { TrendingUp, Activity } from 'lucide-react';

interface QueueTrendChartProps {
  history: HistoricalPoint[];
}

export const QueueTrendChart: React.FC<QueueTrendChartProps> = ({ history }) => {
  return (
    <div className="glass-card rounded-2xl p-5 border border-border/70 bg-slate-950/80">
      <div className="flex items-center justify-between mb-4 pb-3 border-b border-border/60">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-lg bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
            <TrendingUp className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-100 tracking-wide uppercase">
              Traffic Density & Queue Trends
            </h3>
            <p className="text-[11px] text-muted-foreground">
              Real-time time-series telemetry from SUMO simulation
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2 text-xs font-mono text-slate-400">
          <Activity className="w-3.5 h-3.5 text-cyan-400 animate-pulse" />
          <span>{history.length} Live Samples</span>
        </div>
      </div>

      <div className="h-[260px] w-full">
        {history.length === 0 ? (
          <div className="h-full flex items-center justify-center text-xs text-muted-foreground font-mono">
            Awaiting real-time data stream from SUMO Controller...
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={history} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" opacity={0.6} />
              <XAxis
                dataKey="time"
                stroke="#64748b"
                fontSize={10}
                tickLine={false}
                interval="preserveStartEnd"
              />
              <YAxis stroke="#64748b" fontSize={10} tickLine={false} allowDecimals={false} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#090d16',
                  borderColor: '#334155',
                  borderRadius: '0.75rem',
                  fontSize: '11px',
                  fontFamily: 'monospace',
                  boxShadow: '0 8px 24px rgba(0,0,0,0.6)',
                }}
                labelStyle={{ color: '#94a3b8', fontWeight: 'bold' }}
              />
              <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }} />
              <Line
                type="monotone"
                dataKey="totalQueue"
                name="Total Queue"
                stroke="#38bdf8"
                strokeWidth={2.5}
                dot={false}
                activeDot={{ r: 5 }}
              />
              <Line
                type="monotone"
                dataKey="N"
                name="North (N)"
                stroke="#ef4444"
                strokeWidth={1.5}
                dot={false}
              />
              <Line
                type="monotone"
                dataKey="E"
                name="East (E)"
                stroke="#3b82f6"
                strokeWidth={1.5}
                dot={false}
              />
              <Line
                type="monotone"
                dataKey="S"
                name="South (S)"
                stroke="#10b981"
                strokeWidth={1.5}
                dot={false}
              />
              <Line
                type="monotone"
                dataKey="W"
                name="West (W)"
                stroke="#f59e0b"
                strokeWidth={1.5}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
};
