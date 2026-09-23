import React, { useState } from 'react';
import { useTrafficData } from '../hooks/useTrafficData';
import { TopHeader } from './header/TopHeader';
import { ConnectionStatusBanner } from './common/ConnectionStatusBanner';
import { OverviewMetrics } from './metrics/OverviewMetrics';
import { NetworkMapView } from './network/NetworkMapView';
import { JunctionsGrid } from './junctions/JunctionsGrid';
import { QueueTrendChart } from './analytics/QueueTrendChart';
import { RLControllerPanel } from './rl/RLControllerPanel';
import { EventLogPanel } from './logs/EventLogPanel';
import { VehicleFleetMonitor } from './vehicles/VehicleFleetMonitor';
import { JunctionDetailModal } from './junctions/JunctionDetailModal';

export const Dashboard: React.FC = () => {
  const [pollingInterval, setPollingInterval] = useState<number>(1000);
  const [modalJunctionId, setModalJunctionId] = useState<string | null>(null);

  const {
    data,
    isOnline,
    isSumoActive,
    lastSyncTime,
    error,
    history,
    logs,
    selectedJunctionId,
    setSelectedJunctionId,
    refetch,
  } = useTrafficData(pollingInterval);

  const activeJunctionsCount = data ? Object.keys(data.junctions || {}).length : 0;

  const handleSelectJunction = (id: string) => {
    setSelectedJunctionId(id);
    if (id !== 'ALL') {
      setModalJunctionId(id);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-foreground font-inter flex flex-col antialiased selection:bg-blue-600 selection:text-white">
      {/* Top Navigation & Status Header */}
      <TopHeader
        isOnline={isOnline}
        isSumoActive={isSumoActive}
        lastSyncTime={lastSyncTime}
        pollingInterval={pollingInterval}
        onPollingIntervalChange={setPollingInterval}
        onRefresh={refetch}
        activeJunctionsCount={activeJunctionsCount}
      />

      {/* Main Control Center Body */}
      <main className="flex-1 max-w-[1920px] w-full mx-auto px-4 lg:px-6 py-6 space-y-6">
        {/* Offline / Connection Banner */}
        <ConnectionStatusBanner
          isOnline={isOnline}
          isSumoActive={isSumoActive}
          error={error}
          onRefresh={refetch}
        />

        {/* Live Overview KPI Metrics */}
        <OverviewMetrics data={data} isOnline={isOnline} />

        {/* Central Visualization Section: Topology Map + Event Stream */}
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
          {/* Main 2x3 Topology Network Map (2 cols on large screen) */}
          <div className="xl:col-span-2">
            <NetworkMapView
              data={data}
              selectedJunctionId={selectedJunctionId}
              onSelectJunction={handleSelectJunction}
            />
          </div>

          {/* Live Decision Event Stream (1 col) */}
          <div className="xl:col-span-1">
            <EventLogPanel logs={logs} />
          </div>
        </div>

        {/* Time-Series Analytics & Queue Trends */}
        <QueueTrendChart history={history} />

        {/* 6-Junction Real-Time Status Grid */}
        <JunctionsGrid
          data={data}
          selectedJunctionId={selectedJunctionId}
          onSelectJunction={handleSelectJunction}
        />

        {/* Reinforcement Learning & Intelligent Controller Telemetry */}
        <RLControllerPanel data={data} />

        {/* Configured SUMO Vehicle Classes & Fleet Demand */}
        <VehicleFleetMonitor />
      </main>

      {/* Footer */}
      <footer className="border-t border-border/50 py-4 px-6 bg-slate-950/80 text-center text-xs font-mono text-slate-500">
        Smart Traffic Management System • TraCI Engine Connected • Multi-Junction Decentralized AI Control
      </footer>

      {/* Selected Junction Detail Modal */}
      {modalJunctionId && data?.junctions?.[modalJunctionId] && (
        <JunctionDetailModal
          junctionId={modalJunctionId}
          info={data.junctions[modalJunctionId]}
          onClose={() => setModalJunctionId(null)}
          onRefresh={refetch}
        />
      )}
    </div>
  );
};