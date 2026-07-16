import React, { useState, useEffect } from 'react';
import { KPISidebar } from './KPISidebar';
import { TrafficMap } from './TrafficMap';
import { IntersectionPanel } from './IntersectionPanel';
import { TrendChart } from './TrendChart';

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

interface Alert {
  id: string;
  type: 'emergency' | 'warning' | 'info';
  message: string;
  timestamp: Date;
  intersection?: string;
}

const MOCK_INTERSECTIONS: Intersection[] = [
  { id: '1', name: 'Main St & 1st Ave', lat: 40.7128, lng: -74.0060, status: 'smooth', vehicleCount: 12, avgWaitTime: 15, currentPhase: 'N-S', signalTiming: 45 },
  { id: '2', name: 'Broadway & 42nd St', lat: 40.7580, lng: -73.9855, status: 'congested', vehicleCount: 45, avgWaitTime: 85, currentPhase: 'E-W', signalTiming: 20 },
  { id: '3', name: 'Park Ave & 59th St', lat: 40.7614, lng: -73.9776, status: 'moderate', vehicleCount: 28, avgWaitTime: 35, currentPhase: 'N-S', signalTiming: 60 },
  { id: '4', name: '5th Ave & 14th St', lat: 40.7353, lng: -73.9912, status: 'smooth', vehicleCount: 18, avgWaitTime: 22, currentPhase: 'E-W', signalTiming: 30 },
  { id: '5', name: 'Houston St & Lafayette', lat: 40.7244, lng: -73.9942, status: 'moderate', vehicleCount: 33, avgWaitTime: 42, currentPhase: 'N-S', signalTiming: 55 },
];

export const Dashboard: React.FC = () => {
  const [selectedIntersection, setSelectedIntersection] = useState<Intersection | null>(null);
  const [intersections, setIntersections] = useState<Intersection[]>(MOCK_INTERSECTIONS);
  const [alerts, setAlerts] = useState<Alert[]>([
    { id: '1', type: 'emergency', message: 'Accident reported at Broadway & 42nd St', timestamp: new Date(), intersection: '2' },
    { id: '2', type: 'warning', message: 'Heavy traffic detected on Park Ave corridor', timestamp: new Date(Date.now() - 300000), intersection: '3' },
    { id: '3', type: 'info', message: 'AI optimization active on 5th Ave', timestamp: new Date(Date.now() - 600000) },
  ]);
  const [kpis, setKpis] = useState({
    commuteReduction: 23.5,
    aiActive: true,
    activeIntersections: 127,
    averageWaitTime: 32.4,
  });

  // Simulate real-time updates
  useEffect(() => {
    const interval = setInterval(() => {
      setIntersections(prev => prev.map(intersection => {
        const shouldUpdate = Math.random() > 0.7;
        if (!shouldUpdate) return intersection;

        const statusOptions: Array<'smooth' | 'moderate' | 'congested'> = ['smooth', 'moderate', 'congested'];
        const phaseOptions: Array<'N-S' | 'E-W'> = ['N-S', 'E-W'];
        
        return {
          ...intersection,
          status: Math.random() > 0.8 ? statusOptions[Math.floor(Math.random() * statusOptions.length)] : intersection.status,
          vehicleCount: Math.max(5, intersection.vehicleCount + Math.floor(Math.random() * 10 - 5)),
          avgWaitTime: Math.max(10, intersection.avgWaitTime + Math.floor(Math.random() * 20 - 10)),
          currentPhase: Math.random() > 0.9 ? phaseOptions[Math.random() > 0.5 ? 1 : 0] : intersection.currentPhase,
          signalTiming: Math.max(15, intersection.signalTiming + Math.floor(Math.random() * 10 - 5)),
        };
      }));

      // Update KPIs
      setKpis(prev => ({
        ...prev,
        commuteReduction: Math.max(0, Math.min(50, prev.commuteReduction + (Math.random() - 0.5) * 2)),
        averageWaitTime: Math.max(15, Math.min(60, prev.averageWaitTime + (Math.random() - 0.5) * 4)),
      }));
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  const handleIntersectionSelect = (intersection: Intersection) => {
    setSelectedIntersection(intersection);
  };

  const handleManualOverride = (intersectionId: string, action: string) => {
    console.log(`Manual override: ${action} for intersection ${intersectionId}`);
    // Add alert about manual override
    const newAlert: Alert = {
      id: Date.now().toString(),
      type: 'info',
      message: `Manual override: ${action} activated`,
      timestamp: new Date(),
      intersection: intersectionId,
    };
    setAlerts(prev => [newAlert, ...prev.slice(0, 4)]);
  };

  return (
    <div className="min-h-screen bg-background text-foreground font-inter">
      {/* Header */}
      <div className="border-b border-border bg-card/50 backdrop-blur-sm">
        <div className="flex items-center justify-between px-6 py-4">
          <div className="flex items-center space-x-4">
            <div className="w-8 h-8 bg-gradient-primary rounded-lg flex items-center justify-center">
              <span className="text-sm font-bold text-white">T</span>
            </div>
            <div>
              <h1 className="text-2xl font-bold bg-gradient-primary bg-clip-text text-transparent">
                TRAFFIX
              </h1>
              <p className="text-sm text-muted-foreground">AI Traffic Management System</p>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <div className={`w-2 h-2 rounded-full ${kpis.aiActive ? 'bg-success animate-pulse' : 'bg-muted'}`} />
              <span className="text-sm font-medium">
                {kpis.aiActive ? 'AI Active' : 'Manual Mode'}
              </span>
            </div>
            <div className="text-sm text-muted-foreground">
              {new Date().toLocaleTimeString()}
            </div>
          </div>
        </div>
      </div>

      {/* Main Dashboard Grid */}
      <div className="flex h-[calc(100vh-80px)]">
        {/* KPI Sidebar - 15% */}
        <div className="w-80 flex-shrink-0 border-r border-border bg-card/30 backdrop-blur-sm">
          <KPISidebar 
            kpis={kpis} 
            alerts={alerts} 
            intersections={intersections}
          />
        </div>

        {/* Main Map Area - 60% */}
        <div className="flex-1 relative">
          <TrafficMap 
            intersections={intersections}
            selectedIntersection={selectedIntersection}
            onIntersectionSelect={handleIntersectionSelect}
          />
        </div>

        {/* Intersection Details Panel - 25% */}
        <div className="w-96 flex-shrink-0 border-l border-border bg-card/30 backdrop-blur-sm">
          <IntersectionPanel 
            intersection={selectedIntersection}
            onManualOverride={handleManualOverride}
          />
        </div>
      </div>
    </div>
  );
};