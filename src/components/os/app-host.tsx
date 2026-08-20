import type { AppId } from "@/lib/os/apps";
import { AboutApp } from "./apps/about-app";
import { CalcApp } from "./apps/calc-app";
import { CircuitApp } from "./apps/circuit-app";
import { FilesApp } from "./apps/files-app";
import { GroverApp } from "./apps/grover-app";
import { LogicApp } from "./apps/logic-app";
import { RegisterApp } from "./apps/register-app";
import { SchedulerApp } from "./apps/scheduler-app";
import { TaskmgrApp } from "./apps/taskmgr-app";
import { TeleportApp } from "./apps/teleport-app";
import { TerminalApp } from "./apps/terminal-app";

export function AppHost({ id }: { id: AppId }) {
  switch (id) {
    case "register":
      return <RegisterApp />;
    case "circuit":
      return <CircuitApp />;
    case "terminal":
      return <TerminalApp />;
    case "files":
      return <FilesApp />;
    case "scheduler":
      return <SchedulerApp />;
    case "teleport":
      return <TeleportApp />;
    case "grover":
      return <GroverApp />;
    case "calc":
      return <CalcApp />;
    case "logic":
      return <LogicApp />;
    case "taskmgr":
      return <TaskmgrApp />;
    case "about":
      return <AboutApp />;
  }
}
