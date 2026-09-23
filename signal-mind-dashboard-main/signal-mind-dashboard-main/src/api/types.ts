// TypeScript definitions matching SUMO Controller API & Simulation State

export type Direction = 'N' | 'E' | 'S' | 'W';

export interface JunctionCounts {
  N: number;
  E: number;
  S: number;
  W: number;
}

export interface DecisionRecord {
  junction?: string;
  phase: Direction | string;
  green: number;
  start_time?: number;
  end_time?: number;
}

export interface JunctionInfo {
  counts: JunctionCounts;
  last_decision?: DecisionRecord;
  last_served?: JunctionCounts;
}

export interface NetworkStatusResponse {
  timestamp: number;
  counts: JunctionCounts;
  junctions: Record<string, JunctionInfo>;
  last_decision: DecisionRecord;
}

export interface HealthResponse {
  status: string;
  message: string;
}

export interface HistoricalPoint {
  time: string;
  timestamp: number;
  totalQueue: number;
  N: number;
  E: number;
  S: number;
  W: number;
  activeJunctions: number;
  busiestJunction: string;
}

export interface LogEntry {
  id: string;
  timestamp: Date;
  timeStr: string;
  type: 'decision' | 'health' | 'warning' | 'alert';
  junction?: string;
  message: string;
  phase?: string;
  green?: number;
  counts?: JunctionCounts;
}

export interface JunctionNodeMeta {
  id: string;
  label: string;
  x: number;
  y: number;
  type: 'arterial' | 'local' | 'perimeter';
  connectedEdges: string[];
  maxSpeedKmh: number;
  numLanes: number;
}
