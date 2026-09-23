// API Client for Smart Traffic Controller backend
import { HealthResponse, NetworkStatusResponse, DecisionRecord, JunctionCounts } from './types';

// Default to Vite proxy (/api) which forwards to http://127.0.0.1:5000
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

export class TrafficApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl.replace(/\/+$/, '');
  }

  /**
   * Check if backend Flask controller API is healthy and running
   */
  async checkHealth(): Promise<HealthResponse> {
    const response = await fetch(`${this.baseUrl}/health`, {
      method: 'GET',
      headers: { 'Accept': 'application/json' },
      signal: AbortSignal.timeout(2000),
    });

    if (!response.ok) {
      throw new Error(`Health check failed with status: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Fetch complete real-time status of all junctions, queues, and last decisions
   */
  async getStatus(): Promise<NetworkStatusResponse> {
    const response = await fetch(`${this.baseUrl}/get_status`, {
      method: 'GET',
      headers: { 'Accept': 'application/json' },
      signal: AbortSignal.timeout(2000),
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch traffic status: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Manually request or test a decision for a junction
   */
  async requestDecision(junction: string, counts: JunctionCounts): Promise<DecisionRecord> {
    const response = await fetch(`${this.baseUrl}/decide`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify({ junction, counts }),
      signal: AbortSignal.timeout(3000),
    });

    if (!response.ok) {
      throw new Error(`Decision request failed: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }
}

export const trafficApi = new TrafficApiClient();
