import { createServerFn } from "@tanstack/react-start";
import type { QuantumArgs, QuantumRequest, QuantumResult } from "./types";

export const runQuantum = createServerFn({ method: "POST" })
  .validator((data: QuantumRequest) => data)
  .handler(async ({ data }): Promise<QuantumResult> => {
    const { executeQuantum } = await import("./bridge.server");
    return executeQuantum(data);
  });

const RPC_MS = 6000;

export async function qrun(op: string, args?: QuantumArgs): Promise<QuantumResult> {
  const req = runQuantum({ data: { op, args } });
  void req.catch(() => undefined);
  return Promise.race([
    req,
    new Promise<never>((_, reject) => {
      setTimeout(() => reject(new Error("quantum rpc timeout")), RPC_MS);
    }),
  ]);
}
