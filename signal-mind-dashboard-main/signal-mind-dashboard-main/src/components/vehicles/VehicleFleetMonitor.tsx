import React from 'react';
import { Car, Bus, Truck, Bike, Navigation, Route } from 'lucide-react';

const VEHICLE_FLEET_DEFINITIONS = [
  {
    type: 'Sedans & Hatchbacks',
    models: 'car_silver, car_red, car_blue, car_white',
    vClass: 'passenger',
    maxSpeed: '72 km/h (20 m/s)',
    accel: '2.6 - 2.8 m/s²',
    color: '#3b82f6',
    icon: Car,
    distribution: '~55% of traffic',
  },
  {
    type: 'SUVs & Wagons',
    models: 'car_suv',
    vClass: 'passenger',
    maxSpeed: '68 km/h (19 m/s)',
    accel: '2.5 m/s²',
    color: '#60a5fa',
    icon: Car,
    distribution: '~20% of traffic',
  },
  {
    type: 'Commercial Vans',
    models: 'van_white',
    vClass: 'passenger/van',
    maxSpeed: '65 km/h (18 m/s)',
    accel: '2.2 m/s²',
    color: '#94a3b8',
    icon: Car,
    distribution: '~10% of traffic',
  },
  {
    type: 'Public Transit Buses',
    models: 'city_bus, coach_bus',
    vClass: 'bus',
    maxSpeed: '54 - 58 km/h (15-16 m/s)',
    accel: '1.7 - 1.8 m/s²',
    color: '#eab308',
    icon: Bus,
    distribution: '~8% of traffic',
  },
  {
    type: 'Logistics & Freight Trucks',
    models: 'delivery_truck, heavy_truck',
    vClass: 'truck / semitrailer',
    maxSpeed: '48 - 58 km/h (13.5-16 m/s)',
    accel: '1.3 - 2.0 m/s²',
    color: '#f97316',
    icon: Truck,
    distribution: '~5% of traffic',
  },
  {
    type: 'Two-Wheelers',
    models: 'motorcycle',
    vClass: 'motorcycle',
    maxSpeed: '79 km/h (22 m/s)',
    accel: '3.5 m/s²',
    color: '#ef4444',
    icon: Bike,
    distribution: '~2% of traffic',
  },
];

export const VehicleFleetMonitor: React.FC = () => {
  return (
    <div className="glass-card rounded-2xl p-5 border border-border/70 bg-slate-950/80">
      <div className="flex items-center justify-between mb-4 pb-3 border-b border-border/60">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
            <Route className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-100 tracking-wide uppercase">
              SUMO Vehicle Classes & Fleet Demand
            </h3>
            <p className="text-[11px] text-muted-foreground">
              Configured multi-class vehicle distribution (22 flows in multi_junction.rou.xml)
            </p>
          </div>
        </div>

        <span className="text-[11px] font-mono text-slate-400">
          11 Vehicle Models Defined
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {VEHICLE_FLEET_DEFINITIONS.map((v, i) => {
          const Icon = v.icon;
          return (
            <div key={i} className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800/80 flex items-start space-x-3">
              <div 
                className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
                style={{ backgroundColor: `${v.color}20`, color: v.color, border: `1px solid ${v.color}40` }}
              >
                <Icon className="w-4 h-4" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between mb-0.5">
                  <h4 className="text-xs font-bold text-slate-200 truncate">{v.type}</h4>
                  <span className="text-[10px] font-mono text-cyan-400 font-semibold">{v.distribution}</span>
                </div>
                <p className="text-[10px] font-mono text-slate-400 truncate">
                  Types: <span className="text-slate-300">{v.models}</span>
                </p>
                <div className="mt-2 pt-2 border-t border-slate-800/60 flex items-center justify-between text-[10px] font-mono text-slate-500">
                  <span>Max: {v.maxSpeed}</span>
                  <span>Acc: {v.accel}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
