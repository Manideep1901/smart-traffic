import React, { useEffect, useRef, useState } from 'react';
import { Navigation2, MapPin, Circle } from 'lucide-react';

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

interface TrafficMapProps {
  intersections: Intersection[];
  selectedIntersection: Intersection | null;
  onIntersectionSelect: (intersection: Intersection) => void;
}

export const TrafficMap: React.FC<TrafficMapProps> = ({
  intersections,
  selectedIntersection,
  onIntersectionSelect,
}) => {
  const mapRef = useRef<HTMLDivElement>(null);
  const [hoveredIntersection, setHoveredIntersection] = useState<string | null>(null);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'smooth': return 'text-traffic-green';
      case 'moderate': return 'text-traffic-yellow';
      case 'congested': return 'text-traffic-red';
      default: return 'text-muted-foreground';
    }
  };

  const getStatusBg = (status: string) => {
    switch (status) {
      case 'smooth': return 'bg-traffic-green/20 border-traffic-green/50';
      case 'moderate': return 'bg-traffic-yellow/20 border-traffic-yellow/50';
      case 'congested': return 'bg-traffic-red/20 border-traffic-red/50';
      default: return 'bg-muted/20 border-muted/50';
    }
  };

  // Simulate map positioning
  const getIntersectionPosition = (intersection: Intersection, index: number) => {
    const baseX = 20 + (index % 3) * 30;
    const baseY = 20 + Math.floor(index / 3) * 25;
    return {
      left: `${baseX + (intersection.lng + 74) * 15}%`,
      top: `${baseY + (40.8 - intersection.lat) * 40}%`,
    };
  };

  return (
    <div className="h-full relative bg-gradient-to-br from-background via-card to-background">
      {/* Map Background Pattern */}
      <div className="absolute inset-0 opacity-10">
        <div className="w-full h-full bg-gradient-to-br from-primary/20 via-transparent to-accent/20" />
        <div 
          className="absolute inset-0 opacity-30" 
          style={{
            backgroundImage: `
              linear-gradient(90deg, hsl(var(--border)) 1px, transparent 1px),
              linear-gradient(hsl(var(--border)) 1px, transparent 1px)
            `,
            backgroundSize: '50px 50px'
          }}
        />
      </div>

      {/* Map Header */}
      <div className="absolute top-4 left-4 z-10">
        <div className="glass-card px-4 py-2 rounded-lg">
          <div className="flex items-center space-x-2">
            <Navigation2 className="w-4 h-4 text-primary" />
            <span className="text-sm font-medium">NYC Traffic Grid</span>
          </div>
        </div>
      </div>

      {/* Map Controls */}
      <div className="absolute top-4 right-4 z-10 space-y-2">
        <div className="glass-card p-2 rounded-lg space-y-1">
          <button className="w-8 h-8 bg-primary/20 hover:bg-primary/40 rounded flex items-center justify-center transition-colors">
            <span className="text-sm font-bold">+</span>
          </button>
          <button className="w-8 h-8 bg-primary/20 hover:bg-primary/40 rounded flex items-center justify-center transition-colors">
            <span className="text-sm font-bold">−</span>
          </button>
        </div>
      </div>

      {/* Traffic Heatmap Legend */}
      <div className="absolute bottom-4 left-4 z-10">
        <div className="glass-card p-4 rounded-lg">
          <h4 className="text-sm font-medium mb-3">Traffic Status</h4>
          <div className="space-y-2">
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 rounded-full bg-traffic-green" />
              <span className="text-xs">Smooth Flow</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 rounded-full bg-traffic-yellow" />
              <span className="text-xs">Moderate Traffic</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 rounded-full bg-traffic-red" />
              <span className="text-xs">Heavy Congestion</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Map Area */}
      <div ref={mapRef} className="w-full h-full relative overflow-hidden">
        {/* Street Grid Simulation */}
        <svg className="absolute inset-0 w-full h-full pointer-events-none opacity-20">
          <defs>
            <pattern id="grid" width="100" height="100" patternUnits="userSpaceOnUse">
              <path d="M 100 0 L 0 0 0 100" fill="none" stroke="hsl(var(--primary))" strokeWidth="1"/>
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#grid)" />
        </svg>

        {/* Intersection Markers */}
        {intersections.map((intersection, index) => {
          const position = getIntersectionPosition(intersection, index);
          const isSelected = selectedIntersection?.id === intersection.id;
          const isHovered = hoveredIntersection === intersection.id;

          return (
            <div key={intersection.id} className="absolute z-20" style={position}>
              {/* Intersection Glow Effect */}
              <div 
                className={`absolute -inset-4 rounded-full blur-lg transition-all duration-300 ${
                  isSelected || isHovered ? 'opacity-100' : 'opacity-0'
                }`}
                style={{
                  background: `radial-gradient(circle, ${
                    intersection.status === 'smooth' ? 'rgb(34, 197, 94, 0.3)' :
                    intersection.status === 'moderate' ? 'rgb(245, 158, 11, 0.3)' :
                    'rgb(239, 68, 68, 0.3)'
                  } 0%, transparent 70%)`
                }}
              />

              {/* Main Intersection Button */}
              <button
                onClick={() => onIntersectionSelect(intersection)}
                onMouseEnter={() => setHoveredIntersection(intersection.id)}
                onMouseLeave={() => setHoveredIntersection(null)}
                className={`
                  relative w-12 h-12 rounded-full border-2 transition-all duration-300 hover-glow
                  ${getStatusBg(intersection.status)}
                  ${isSelected ? 'scale-125 ring-2 ring-primary ring-offset-2 ring-offset-background' : 'hover:scale-110'}
                `}
              >
                <MapPin className={`w-6 h-6 mx-auto ${getStatusColor(intersection.status)}`} />
                
                {/* Signal Phase Indicator */}
                <div className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-background border border-border flex items-center justify-center">
                  <div className={`w-2 h-2 rounded-full ${
                    intersection.currentPhase === 'N-S' ? 'bg-success' : 'bg-warning'
                  }`} />
                </div>

                {/* Vehicle Count Badge */}
                <div className="absolute -bottom-1 -right-1 px-1.5 py-0.5 bg-background border border-border rounded-full">
                  <span className="text-xs font-medium">{intersection.vehicleCount}</span>
                </div>
              </button>

              {/* Intersection Label */}
              {(isHovered || isSelected) && (
                <div className="absolute top-14 left-1/2 transform -translate-x-1/2 glass-card px-2 py-1 rounded whitespace-nowrap animate-fade-in-up">
                  <div className="text-xs font-medium">{intersection.name}</div>
                  <div className="text-xs text-muted-foreground">
                    Wait: {intersection.avgWaitTime}s | Phase: {intersection.currentPhase}
                  </div>
                </div>
              )}

              {/* Traffic Flow Animation */}
              <div className="absolute inset-0 pointer-events-none">
                {[...Array(3)].map((_, i) => (
                  <div
                    key={i}
                    className={`absolute w-1 h-1 rounded-full ${getStatusColor(intersection.status).replace('text-', 'bg-')} animate-pulse`}
                    style={{
                      left: `${20 + i * 15}%`,
                      top: `${20 + i * 15}%`,
                      animationDelay: `${i * 0.5}s`,
                      animationDuration: `${2 + intersection.status === 'congested' ? 1 : 0}s`,
                    }}
                  />
                ))}
              </div>
            </div>
          );
        })}

        {/* Traffic Flow Lines */}
        <svg className="absolute inset-0 w-full h-full pointer-events-none opacity-30">
          {intersections.map((intersection, index) => {
            if (index < intersections.length - 1) {
              const pos1 = getIntersectionPosition(intersection, index);
              const pos2 = getIntersectionPosition(intersections[index + 1], index + 1);
              
              return (
                <line
                  key={`flow-${intersection.id}`}
                  x1={`calc(${pos1.left} + 24px)`}
                  y1={`calc(${pos1.top} + 24px)`}
                  x2={`calc(${pos2.left} + 24px)`}
                  y2={`calc(${pos2.top} + 24px)`}
                  stroke="hsl(var(--primary))"
                  strokeWidth="2"
                  strokeDasharray="5,5"
                  className="animate-pulse"
                />
              );
            }
            return null;
          })}
        </svg>
      </div>
    </div>
  );
};