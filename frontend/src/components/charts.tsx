"use client";

import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const axisStyle = { fontSize: 11, fill: "var(--mist)" };

export function EquityCurveChart({ data }: { data: Array<{ timestamp: string; equity: number }> }) {
  const points = data.map((d) => ({ date: d.timestamp.slice(0, 10), equity: d.equity }));
  return (
    <ResponsiveContainer width="100%" height={260}>
      <LineChart data={points} margin={{ top: 8, right: 12, bottom: 0, left: 0 }}>
        <CartesianGrid stroke="var(--line)" strokeDasharray="3 3" vertical={false} />
        <XAxis dataKey="date" tick={axisStyle} tickLine={false} axisLine={{ stroke: "var(--line)" }} minTickGap={24} />
        <YAxis tick={axisStyle} tickLine={false} axisLine={false} width={64} />
        <Tooltip
          contentStyle={{
            background: "var(--ink-2)",
            border: "1px solid var(--glass-border)",
            borderRadius: 10,
            fontSize: 12,
          }}
          labelStyle={{ color: "var(--mist)" }}
        />
        <ReferenceLine y={0} stroke="var(--line)" />
        <Line type="monotone" dataKey="equity" stroke="#3987e5" strokeWidth={2} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}

export function RollingSharpeChart({ data }: { data: Array<{ date: string; sharpe: number }> }) {
  return (
    <ResponsiveContainer width="100%" height={220}>
      <LineChart data={data} margin={{ top: 8, right: 12, bottom: 0, left: 0 }}>
        <CartesianGrid stroke="var(--line)" strokeDasharray="3 3" vertical={false} />
        <XAxis dataKey="date" tick={axisStyle} tickLine={false} axisLine={{ stroke: "var(--line)" }} minTickGap={24} />
        <YAxis tick={axisStyle} tickLine={false} axisLine={false} width={40} />
        <Tooltip
          contentStyle={{
            background: "var(--ink-2)",
            border: "1px solid var(--glass-border)",
            borderRadius: 10,
            fontSize: 12,
          }}
          labelStyle={{ color: "var(--mist)" }}
        />
        <ReferenceLine y={0.5} stroke="var(--warn)" strokeDasharray="4 4" />
        <Line type="monotone" dataKey="sharpe" stroke="#d95926" strokeWidth={2} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}
