"use client";

import { useState } from "react";

export default function BacktestPage() {
  const [running, setRunning] = useState(false);
  const [results, setResults] = useState<unknown>(null);

  const handleRun = async () => {
    setRunning(true);
    try {
      const res = await fetch("http://127.0.0.1:8000/api/backtest/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ initial_capital: 100000, months: 6 })
      });
      const data = await res.json();
      setResults(data);
    } catch (e) {
      console.error(e);
    }
    setRunning(false);
  };

  return (
    <div className="space-y-6 font-mono">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-primary">STRATEGY BACKTESTING</h1>
        <p className="text-sm text-muted-foreground mt-1">Run historical validation on top conviction picks</p>
      </div>

      <div className="border border-border/50 rounded-md bg-card/50 p-6 flex flex-col items-center justify-center min-h-[300px] space-y-6">
        <div className="text-center space-y-2">
          <h2 className="text-lg font-bold">Run 6-Month Historical Backtest</h2>
          <p className="text-sm text-muted-foreground max-w-md">
            This will simulate investing $100,000 into the top 10 highest conviction scored equities exactly 6 months ago, and compare the performance against the SPY benchmark.
          </p>
        </div>
        
        <button 
          onClick={handleRun} 
          disabled={running}
          className="bg-primary text-primary-foreground font-bold px-6 py-2 rounded-md hover:bg-primary/90 transition-colors disabled:opacity-50"
        >
          {running ? "Executing Simulation..." : "RUN BACKTEST"}
        </button>

        {results !== null && (
          <div className="w-full mt-8 p-4 border border-border/50 rounded bg-[#0a0a0b]">
            <pre className="text-xs text-muted-foreground overflow-x-auto">
              {JSON.stringify(results, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}
