import { useState, useEffect, useRef, useCallback } from 'react';
import { trafficApi } from '../api/trafficApi';
import { NetworkStatusResponse, HistoricalPoint, LogEntry, Direction } from '../api/types';

export function useTrafficData(pollingIntervalMs: number = 1000) {
  const [data, setData] = useState<NetworkStatusResponse | null>(null);
  const [isOnline, setIsOnline] = useState<boolean>(false);
  const [isSumoActive, setIsSumoActive] = useState<boolean>(false);
  const [lastSyncTime, setLastSyncTime] = useState<Date | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<HistoricalPoint[]>([]);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [selectedJunctionId, setSelectedJunctionId] = useState<string>('ALL');

  // Track previous decision timestamps to detect new events
  const lastDecisionsRef = useRef<Record<string, number>>({});
  const initialMountRef = useRef<boolean>(true);

  const fetchTrafficStatus = useCallback(async () => {
    try {
      // First, check status
      const statusData = await trafficApi.getStatus();
      setData(statusData);
      setIsOnline(true);
      setError(null);
      const now = new Date();
      setLastSyncTime(now);

      const timeStr = now.toLocaleTimeString();
      const junctions = statusData.junctions || {};
      const junctionIds = Object.keys(junctions);
      
      // Determine if SUMO is actively pushing updates (junction counts or decisions present)
      const hasActiveJunctions = junctionIds.length > 0;
      setIsSumoActive(hasActiveJunctions);

      // Compute total queues
      const totalN = statusData.counts?.N || 0;
      const totalE = statusData.counts?.E || 0;
      const totalS = statusData.counts?.S || 0;
      const totalW = statusData.counts?.W || 0;
      const totalQueue = totalN + totalE + totalS + totalW;

      // Find busiest junction
      let maxQueue = -1;
      let busiest = 'None';
      junctionIds.forEach((id) => {
        const jCounts = junctions[id].counts || { N: 0, E: 0, S: 0, W: 0 };
        const qSum = jCounts.N + jCounts.E + jCounts.S + jCounts.W;
        if (qSum > maxQueue) {
          maxQueue = qSum;
          busiest = id;
        }
      });

      // Update historical points (keep last 60 points)
      setHistory((prev) => {
        const newPoint: HistoricalPoint = {
          time: timeStr,
          timestamp: Date.now(),
          totalQueue,
          N: totalN,
          E: totalE,
          S: totalS,
          W: totalW,
          activeJunctions: junctionIds.length,
          busiestJunction: busiest,
        };
        const updated = [...prev, newPoint];
        return updated.length > 60 ? updated.slice(updated.length - 60) : updated;
      });

      // Inspect junctions for new decisions to append to event log
      const newLogs: LogEntry[] = [];
      junctionIds.forEach((jId) => {
        const jInfo = junctions[jId];
        const dec = jInfo.last_decision;
        if (dec && dec.start_time) {
          const prevStart = lastDecisionsRef.current[jId] || 0;
          if (dec.start_time > prevStart) {
            lastDecisionsRef.current[jId] = dec.start_time;
            
            // Only add log after initial load
            if (!initialMountRef.current) {
              newLogs.push({
                id: `${jId}-${dec.start_time}-${Math.random()}`,
                timestamp: now,
                timeStr,
                type: 'decision',
                junction: jId,
                phase: dec.phase,
                green: dec.green,
                counts: jInfo.counts,
                message: `[${jId}] Green phase allocated to direction ${dec.phase} for ${dec.green}s (Queues: N:${jInfo.counts.N} E:${jInfo.counts.E} S:${jInfo.counts.S} W:${jInfo.counts.W})`,
              });
            }
          }
        }
      });

      if (initialMountRef.current) {
        initialMountRef.current = false;
        newLogs.push({
          id: `init-${Date.now()}`,
          timestamp: now,
          timeStr,
          type: 'health',
          message: `Connected to Smart Traffic Controller API. Discovered ${junctionIds.length} active junctions.`,
        });
      }

      if (newLogs.length > 0) {
        setLogs((prev) => [...newLogs, ...prev].slice(0, 100));
      }
    } catch (err: any) {
      setIsOnline(false);
      setIsSumoActive(false);
      setError(err?.message || 'Failed to connect to Controller API');
    }
  }, []);

  // Polling loop
  useEffect(() => {
    fetchTrafficStatus();
    const interval = setInterval(fetchTrafficStatus, pollingIntervalMs);
    return () => clearInterval(interval);
  }, [fetchTrafficStatus, pollingIntervalMs]);

  return {
    data,
    isOnline,
    isSumoActive,
    lastSyncTime,
    error,
    history,
    logs,
    selectedJunctionId,
    setSelectedJunctionId,
    refetch: fetchTrafficStatus,
  };
}
