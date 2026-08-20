export type Gate = {
  g: string;
  q?: number;
  t?: number;
  c?: number;
  theta?: number;
  controls?: number[];
};

export type Bloch = { x: number; y: number; z: number; purity: number };

export type Amp = { bit: string; re: number; im: number; p: number };

export type QuantumArgs = {
  name?: string;
  app_id?: number;
  pids?: number[];
  n?: number;
  text?: string;
  gates?: Gate[];
  shots?: number;
  seed?: number;
  commit?: boolean;
  theta?: number;
  phi?: number;
  marked?: number;
  iters?: number;
  a?: number;
  b?: number;
  bits?: string;
  alu_op?: string;
  width?: number;
};

export type QuantumRequest = {
  op: string;
  args?: QuantumArgs;
};

export type GroverStep = { iter: number; p_marked: number; amps?: Amp[] };

export type QuantumResult = {
  backend?: string;
  version?: string;
  engine?: string;
  n?: number;
  n_qubits?: number;
  allocated?: number;
  fidelity?: number;
  noise?: boolean;
  shots_model?: string;
  boot_bits?: string | null;
  boot_ok?: boolean;
  syscalls?: number;
  log?: string[];
  bloch?: Bloch[];
  amps?: Amp[];
  counts?: Record<string, number>;
  qasm?: string;
  gate_count?: number;
  collapsed?: string;
  bits?: string;
  alu_op?: string;
  result?: number;
  carry?: number;
  zero?: boolean;
  width?: number;
  entropy?: number;
  occupancy?: number;
  idle?: boolean;
  fallback?: boolean;
  error?: string;
};
