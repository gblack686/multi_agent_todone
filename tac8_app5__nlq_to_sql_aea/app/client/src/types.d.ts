// These must match the Pydantic models exactly

// File Upload Types
export interface FileUploadResponse {
  table_name: string;
  table_schema: Record<string, string>;
  row_count: number;
  sample_data: Record<string, any>[];
  error?: string;
}

// Query Types
export interface QueryRequest {
  query: string;
  llm_provider: "openai" | "anthropic";
  table_name?: string;
}

export interface QueryResponse {
  sql: string;
  results: Record<string, any>[];
  columns: string[];
  row_count: number;
  execution_time_ms: number;
  error?: string;
}

// Database Schema Types
export interface ColumnInfo {
  name: string;
  type: string;
  nullable: boolean;
  primary_key: boolean;
}

export interface TableSchema {
  name: string;
  columns: ColumnInfo[];
  row_count: number;
  created_at: string;
}

export interface DatabaseSchemaResponse {
  tables: TableSchema[];
  total_tables: number;
  error?: string;
}

// Insights Types
export interface InsightsRequest {
  table_name: string;
  column_names?: string[];
}

export interface ColumnInsight {
  column_name: string;
  data_type: string;
  unique_values: number;
  null_count: number;
  min_value?: any;
  max_value?: any;
  avg_value?: number;
  most_common?: Record<string, any>[];
}

export interface InsightsResponse {
  table_name: string;
  insights: ColumnInsight[];
  generated_at: string;
  error?: string;
}

// Random Query Generation Types
export interface RandomQueryResponse {
  query: string;
  error?: string;
}

// Health Check Types
export interface HealthCheckResponse {
  status: "ok" | "error";
  database_connected: boolean;
  tables_count: number;
  version: string;
  uptime_seconds: number;
}

// Data Generation Types
export interface DataGenerationResponse {
  success: boolean;
  rows_generated: number;
  message: string;
  error?: string;
}

// AEA Agent Types
export interface AEAAgent {
  id: number;
  agent_id: string;
  agent_name?: string;  // AI-generated name for the agent
  adw_id: string;
  cc_session_id?: string;  // Claude Code session ID (set after first prompt)
  conversation: AEAMessage[];
  full_output?: string;
  state: 'idle' | 'working' | 'errored' | 'archived';
  created_at: string;
  updated_at: string;
  archived: boolean;
}

export interface AEAMessage {
  who: 'user' | 'agent';
  content: string;
  created: string;
}

export interface AEAPromptRequest {
  agent_id: string;
  prompt: string;
}

export interface AEAPromptResponse {
  success: boolean;
  agent: AEAAgent;
  error?: string;
}

export interface AEANewAgentResponse {
  agent: AEAAgent;
}

export interface AEAServerStatus {
  running: boolean;
  version?: string;
}