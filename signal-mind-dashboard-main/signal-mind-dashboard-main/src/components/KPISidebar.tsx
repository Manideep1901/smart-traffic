import React from 'react';
import { AlertTriangle, Activity, Clock, TrendingUp, Zap } from 'lucide-react';
import { TrendChart } from './TrendChart';

interface KPISidebarProps {
  kpis: {
    commuteReduction: number;
    aiActive: boolean;
    activeIntersections: number;
    averageWaitTime: number;
  };
  alerts: Array<{
    id: string;
    type: 'emergency' | 'warning' | 'info';
    message: string;
    timestamp: Date;
    intersection?: string;
  }>;
  intersections: Array<{
    id: string;
    status: 'smooth' | 'moderate' | 'congested';
  }>;
}

export const KPISidebar: React.FC<KPISidebarProps> = ({ kpis, alerts, intersections }) => {
  const getAlertIcon = (type: string) => {
    switch (type) {
      case 'emergency': return <AlertTriangle className="w-4 h-4" />;
      case 'warning': return <Clock className="w-4 h-4" />;
      default: return <Activity className="w-4 h-4" />;
    }
  };

  const getAlertStyle = (type: string) => {
    switch (type) {
      case 'emergency': return 'border-destructive/50 bg-destructive/10 text-destructive-foreground pulse-alert';
      case 'warning': return 'border-warning/50 bg-warning/10 text-warning-foreground';
      default: return 'border-primary/50 bg-primary/10 text-primary-foreground';
    }
  };

  const trafficStats = {
    smooth: intersections.filter(i => i.status === 'smooth').length,
    moderate: intersections.filter(i => i.status === 'moderate').length,
    congested: intersections.filter(i => i.status === 'congested').length,
  };

  return (
    <div className="h-full flex flex-col p-6 space-y-6 overflow-y-auto">
      {/* Primary KPI - Commute Time Reduction */}
      <div className="kpi-card animate-fade-in-up">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-medium text-muted-foreground">Commute Time Reduction</h3>
          <TrendingUp className="w-4 h-4 text-success" />
        </div>
        <div className="space-y-2">
          <div className="text-4xl font-bold text-success">
            {kpis.commuteReduction.toFixed(1)}%
          </div>
          <div className="w-full bg-muted rounded-full h-2">
            <div 
              className="bg-gradient-to-r from-success to-success/80 h-2 rounded-full transition-all duration-500"
              style={{ width: `${Math.min(kpis.commuteReduction * 2, 100)}%` }}
            />
          </div>
        </div>
      </div>

      {/* System Status */}
      <div className="kpi-card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-medium text-muted-foreground">System Status</h3>
          <Zap className={`w-4 h-4 ${kpis.aiActive ? 'text-success' : 'text-muted-foreground'}`} />
        </div>
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm">AI Mode</span>
            <div className={`px-2 py-1 rounded-full text-xs font-medium ${
              kpis.aiActive ? 'bg-success/20 text-success' : 'bg-muted text-muted-foreground'
            }`}>
              {kpis.aiActive ? 'Active' : 'Inactive'}
            </div>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm">Active Intersections</span>
            <span className="text-sm font-semibold">{kpis.activeIntersections}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm">Avg Wait Time</span>
            <span className="text-sm font-semibold">{kpis.averageWaitTime.toFixed(1)}s</span>
          </div>
        </div>
      </div>

      {/* Traffic Distribution */}
      <div className="kpi-card">
        <h3 className="text-sm font-medium text-muted-foreground mb-4">Traffic Distribution</h3>
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 rounded-full bg-traffic-green" />
              <span className="text-sm">Smooth</span>
            </div>
            <span className="text-sm font-semibold">{trafficStats.smooth}</span>
          </div>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 rounded-full bg-traffic-yellow" />
              <span className="text-sm">Moderate</span>
            </div>
            <span className="text-sm font-semibold">{trafficStats.moderate}</span>
          </div>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 rounded-full bg-traffic-red" />
              <span className="text-sm">Congested</span>
            </div>
            <span className="text-sm font-semibold">{trafficStats.congested}</span>
          </div>
        </div>
      </div>

      {/* Traffic Trend Chart */}
      <div className="kpi-card">
        <h3 className="text-sm font-medium text-muted-foreground mb-4">Traffic Trend (3h)</h3>
        <TrendChart />
      </div>

      {/* Live Alerts */}
      <div className="kpi-card flex-1">
        <h3 className="text-sm font-medium text-muted-foreground mb-4">Live Alerts</h3>
        <div className="space-y-3">
          {alerts.slice(0, 5).map((alert) => (
            <div
              key={alert.id}
              className={`p-3 rounded-lg border ${getAlertStyle(alert.type)} transition-all duration-200`}
            >
              <div className="flex items-start space-x-2">
                {getAlertIcon(alert.type)}
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-medium leading-tight">{alert.message}</p>
                  <p className="text-xs opacity-75 mt-1">
                    {alert.timestamp.toLocaleTimeString()}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};