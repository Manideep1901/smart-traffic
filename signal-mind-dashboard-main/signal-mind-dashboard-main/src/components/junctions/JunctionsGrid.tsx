import React from 'react';
import { NetworkStatusResponse } from '../../api/types';
import { JunctionCard } from './JunctionCard';
import { Network } from 'lucide-react';

interface JunctionsGridProps {
  data: NetworkStatusResponse | null;
  selectedJunctionId: string;
  onSelectJunction: (id: string) => void;
}

const JUNCTION_METADATA = [
  { id: 'J1', name: 'Central West Junction', roadType: '3-Lane Highway & Diagonal Arterial' },
  { id: 'J2', name: 'Central Plaza Hub', roadType: '3-Lane Highway & N2 Corridor' },
  { id: 'J3', name: 'Highway Interchange', roadType: '3-Lane Highway & Vertical Expressway' },
  { id: 'J4', name: 'Southwest Local Node', roadType: '2-Lane Local Street & S1 Connector' },
  { id: 'J5', name: 'South Central Avenue', roadType: '2-Lane Local Street & S2 Connector' },
  { id: 'J6', name: 'Southeast Express Node', roadType: '2-Lane Local & Vertical Expressway' },
];

export const JunctionsGrid: React.FC<JunctionsGridProps> = ({
  data,
  selectedJunctionId,
  onSelectJunction,
}) => {
  const junctions = data?.junctions || {};

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Network className="w-5 h-5 text-blue-400" />
          <h2 className="text-base font-bold text-slate-100 tracking-wide uppercase">
            Junction Real-Time Status (J1 – J6)
          </h2>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => onSelectJunction('ALL')}
            className={`px-3 py-1 rounded-lg text-xs font-mono font-medium transition-all ${
              selectedJunctionId === 'ALL'
                ? 'bg-blue-600 text-white shadow-sm'
                : 'bg-slate-800 text-slate-400 hover:text-white'
            }`}
          >
            Show All
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {JUNCTION_METADATA.map((meta) => (
          <JunctionCard
            key={meta.id}
            id={meta.id}
            name={meta.name}
            roadType={meta.roadType}
            info={junctions[meta.id]}
            isSelected={selectedJunctionId === meta.id}
            onSelect={onSelectJunction}
          />
        ))}
      </div>
    </div>
  );
};
