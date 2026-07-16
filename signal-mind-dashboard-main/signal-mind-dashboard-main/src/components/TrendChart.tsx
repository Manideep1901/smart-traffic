import React, { useMemo } from 'react';
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer } from 'recharts';

export const TrendChart: React.FC = () => {
  const data = useMemo(() => {
    const now = new Date();
    const points = [];
    
    for (let i = 18; i >= 0; i--) {
      const time = new Date(now.getTime() - i * 10 * 60 * 1000); // 10-minute intervals
      const baseTraffic = 30 + Math.sin(i * 0.3) * 15; // Simulate traffic patterns
      const noise = (Math.random() - 0.5) * 10;
      
      points.push({
        time: time.toLocaleTimeString('en-US', { 
          hour: '2-digit', 
          minute: '2-digit',
          hour12: false 
        }),
        traffic: Math.max(5, Math.min(80, baseTraffic + noise)),
      });
    }
    
    return points;
  }, []);

  return (
    <div className="h-24">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <XAxis 
            dataKey="time" 
            hide
          />
          <YAxis 
            hide
            domain={[0, 80]}
          />
          <Line
            type="monotone"
            dataKey="traffic"
            stroke="hsl(var(--primary))"
            strokeWidth={2}
            dot={false}
            activeDot={{
              r: 3,
              fill: "hsl(var(--primary))",
              stroke: "hsl(var(--background))",
              strokeWidth: 2,
            }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};