import React, { useState, useEffect } from 'react';
import { 
  MapPin, 
  Car, 
  Clock, 
  Activity, 
  Camera, 
  Settings, 
  AlertTriangle,
  Play,
  Square,
  RotateCcw
} from 'lucide-react';
import { Button } from '@/components/ui/button';

interface Intersection {
  id: string;
  name: string;
  lat: number;
  lng: number;
  status: 'smooth' | 'moderate' | 'congested';
  vehicleCount: number;
  avgWaitTime: number;
  currentPhase: 'N-S' | 'E-W';
  signalTiming: number;
}

interface IntersectionPanelProps {
  intersection: Intersection | null;
  onManualOverride: (intersectionId: string, action: string) => void;
}

interface AIDecision {
  id: string;
  timestamp: Date;
  action: string;
  reason: string;
  confidence: number;
}

export const IntersectionPanel: React.FC<IntersectionPanelProps> = ({
  intersection,
  onManualOverride,
}) => {
  const [aiDecisions, setAiDecisions] = useState<AIDecision[]>([]);
  const [liveStats, setLiveStats] = useState({
    northbound: 0,
    southbound: 0,
    eastbound: 0,
    westbound: 0,
  });

  // Simulate AI decisions and live stats
  useEffect(() => {
    if (!intersection) return;

    const interval = setInterval(() => {
      // Update live vehicle counts
      setLiveStats({
        northbound: Math.floor(Math.random() * 20) + 5,
        southbound: Math.floor(Math.random() * 20) + 5,
        eastbound: Math.floor(Math.random() * 20) + 5,
        westbound: Math.floor(Math.random() * 20) + 5,
      });

      // Occasionally add AI decisions
      if (Math.random() > 0.7) {
        const actions = [
          'Extended N-S green phase',
          'Optimized signal timing',
          'Adjusted for heavy traffic',
          'Emergency vehicle priority',
          'Peak hour optimization',
        ];
        
        const reasons = [
          'Detected increasing queue length',
          'Historical pattern analysis',
          'Real-time congestion detected',
          'Emergency services request',
          'Predictive traffic modeling',
        ];

        const newDecision: AIDecision = {
          id: Date.now().toString(),
          timestamp: new Date(),
          action: actions[Math.floor(Math.random() * actions.length)],
          reason: reasons[Math.floor(Math.random() * reasons.length)],
          confidence: 0.75 + Math.random() * 0.24, // 75-99% confidence
        };

        setAiDecisions(prev => [newDecision, ...prev.slice(0, 4)]);
      }
    }, 4000);

    return () => clearInterval(interval);
  }, [intersection]);

  if (!intersection) {
    return (
      <div className="h-full flex items-center justify-center text-center p-6">
        <div className="space-y-4">
          <MapPin className="w-12 h-12 text-muted-foreground mx-auto" />
          <div>
            <h3 className="text-lg font-medium text-muted-foreground">No Intersection Selected</h3>
            <p className="text-sm text-muted-foreground mt-2">
              Click on any intersection marker on the map to view detailed information and controls.
            </p>
          </div>
        </div>
      </div>
    );
  }

  const getStatusStyle = (status: string) => {
    switch (status) {
      case 'smooth': return 'text-traffic-green border-traffic-green bg-traffic-green/10';
      case 'moderate': return 'text-traffic-yellow border-traffic-yellow bg-traffic-yellow/10';
      case 'congested': return 'text-traffic-red border-traffic-red bg-traffic-red/10';
      default: return 'text-muted-foreground border-muted bg-muted/10';
    }
  };

  return (
    <div className="h-full flex flex-col p-6 space-y-6 overflow-y-auto animate-slide-in-right">
      {/* Header */}
      <div className="space-y-4">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-xl font-bold text-foreground">{intersection.name}</h2>
            <p className="text-sm text-muted-foreground mt-1">
              ID: {intersection.id} • Lat: {intersection.lat.toFixed(4)}, Lng: {intersection.lng.toFixed(4)}
            </p>
          </div>
          <div className={`px-3 py-1 rounded-full border text-sm font-medium ${getStatusStyle(intersection.status)}`}>
            {intersection.status.toUpperCase()}
          </div>
        </div>

        {/* Current Signal Phase */}
        <div className="glass-card p-4 rounded-lg">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-medium text-muted-foreground">Current Signal Phase</h3>
            <Activity className="w-4 h-4 text-primary" />
          </div>
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm">Active Direction</span>
              <span className="text-sm font-semibold text-primary">{intersection.currentPhase}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm">Remaining Time</span>
              <span className="text-sm font-semibold">{intersection.signalTiming}s</span>
            </div>
            <div className="w-full bg-muted rounded-full h-2 mt-2">
              <div 
                className="bg-gradient-primary h-2 rounded-full transition-all duration-1000"
                style={{ width: `${(intersection.signalTiming / 90) * 100}%` }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Live Camera Feed */}
      <div className="glass-card p-4 rounded-lg">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-medium text-muted-foreground">Live Camera Feed</h3>
          <Camera className="w-4 h-4 text-primary" />
        </div>
        <div className="aspect-video bg-gradient-to-br from-muted/50 to-muted rounded-lg overflow-hidden relative">
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center space-y-2">
              <Camera className="w-8 h-8 text-muted-foreground mx-auto" />
              <p className="text-xs text-muted-foreground">Camera Feed Simulated</p>
            </div>
          </div>
          {/* Simulated traffic overlay */}
          <div className="absolute bottom-2 left-2 right-2 flex justify-between text-xs">
            <div className="bg-background/80 px-2 py-1 rounded">Live</div>
            <div className="bg-background/80 px-2 py-1 rounded">HD</div>
          </div>
        </div>
      </div>

      {/* Key Statistics */}
      <div className="glass-card p-4 rounded-lg">
        <h3 className="text-sm font-medium text-muted-foreground mb-4">Traffic Statistics</h3>
        <div className="grid grid-cols-2 gap-4">
          <div className="text-center">
            <Car className="w-5 h-5 text-primary mx-auto mb-1" />
            <div className="text-lg font-bold">{intersection.vehicleCount}</div>
            <div className="text-xs text-muted-foreground">Total Vehicles</div>
          </div>
          <div className="text-center">
            <Clock className="w-5 h-5 text-primary mx-auto mb-1" />
            <div className="text-lg font-bold">{intersection.avgWaitTime}s</div>
            <div className="text-xs text-muted-foreground">Avg Wait Time</div>
          </div>
        </div>
      </div>

      {/* Lane-by-Lane Count */}
      <div className="glass-card p-4 rounded-lg">
        <h3 className="text-sm font-medium text-muted-foreground mb-4">Lane Vehicle Count</h3>
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm">Northbound</span>
            <span className="text-sm font-semibold">{liveStats.northbound}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm">Southbound</span>
            <span className="text-sm font-semibold">{liveStats.southbound}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm">Eastbound</span>
            <span className="text-sm font-semibold">{liveStats.eastbound}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm">Westbound</span>
            <span className="text-sm font-semibold">{liveStats.westbound}</span>
          </div>
        </div>
      </div>

      {/* AI Decision Log */}
      <div className="glass-card p-4 rounded-lg flex-1">
        <h3 className="text-sm font-medium text-muted-foreground mb-4">AI Decision Log</h3>
        <div className="space-y-3">
          {aiDecisions.length === 0 ? (
            <p className="text-xs text-muted-foreground text-center py-4">
              Monitoring traffic patterns...
            </p>
          ) : (
            aiDecisions.map((decision) => (
              <div key={decision.id} className="border border-border rounded-lg p-3 space-y-2">
                <div className="flex items-start justify-between">
                  <span className="text-sm font-medium text-foreground">{decision.action}</span>
                  <span className={`text-xs px-2 py-1 rounded-full font-medium ${
                    decision.confidence > 0.9 ? 'bg-success/20 text-success' : 'bg-warning/20 text-warning'
                  }`}>
                    {(decision.confidence * 100).toFixed(0)}%
                  </span>
                </div>
                <p className="text-xs text-muted-foreground">{decision.reason}</p>
                <p className="text-xs text-muted-foreground">
                  {decision.timestamp.toLocaleTimeString()}
                </p>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Manual Override Controls */}
      <div className="glass-card p-4 rounded-lg">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-medium text-muted-foreground">Manual Override</h3>
          <AlertTriangle className="w-4 h-4 text-warning" />
        </div>
        <div className="space-y-2">
          <Button
            variant="outline"
            size="sm"
            className="w-full hover-glow"
            onClick={() => onManualOverride(intersection.id, 'Force N-S Green 30s')}
          >
            <Play className="w-4 h-4 mr-2" />
            Force N-S Green (30s)
          </Button>
          <Button
            variant="outline"
            size="sm"
            className="w-full hover-glow"
            onClick={() => onManualOverride(intersection.id, 'Force E-W Green 30s')}
          >
            <Play className="w-4 h-4 mr-2" />
            Force E-W Green (30s)
          </Button>
          <Button
            variant="outline"
            size="sm"
            className="w-full hover-glow"
            onClick={() => onManualOverride(intersection.id, 'Emergency Stop All')}
          >
            <Square className="w-4 h-4 mr-2" />
            Emergency Stop
          </Button>
          <Button
            variant="outline"
            size="sm"
            className="w-full hover-glow"
            onClick={() => onManualOverride(intersection.id, 'Return to AI Control')}
          >
            <RotateCcw className="w-4 h-4 mr-2" />
            Return to AI
          </Button>
        </div>
      </div>
    </div>
  );
};