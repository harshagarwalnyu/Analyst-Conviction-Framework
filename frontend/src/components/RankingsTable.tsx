"use client";

import { useMemo } from "react";
import Link from "next/link";
import { usePriceStream } from "@/hooks/usePriceStream";
import type { Ranking } from "@/lib/api";

export function RankingsTable({ initialRankings }: { initialRankings: Ranking[] }) {
  const symbols = useMemo(() => initialRankings.map((r) => r.ticker), [initialRankings]);
  const livePrices = usePriceStream(symbols);

  return (
    <div className="rounded-md border border-border/50 overflow-hidden bg-card/50">
      <table className="w-full text-sm text-left">
        <thead className="bg-muted/30 text-muted-foreground text-[10px] uppercase font-mono border-b border-border/50">
          <tr>
            <th className="px-4 py-3 font-medium">Ticker</th>
            <th className="px-4 py-3 font-medium">Score</th>
            <th className="px-4 py-3 font-medium text-right">Price</th>
            <th className="px-4 py-3 font-medium text-right">Target</th>
            <th className="px-4 py-3 font-medium text-right">Upside</th>
            <th className="px-4 py-3 font-medium">Signal</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border/50 font-mono">
          {initialRankings.map((r) => {
            const price = livePrices[r.ticker] || r.raw_data.current_price;
            const target = r.raw_data.target_mean;
            const upside = target && target > 0 && price > 0 ? ((target - price) / price) * 100 : 0;
            const upsideColor = upside > 0 ? "text-green-500" : "text-red-500";
            
            // Score bar
            const scorePct = Math.max(0, Math.min(100, r.conviction_score));

            return (
              <tr key={r.ticker} className="hover:bg-muted/30 transition-colors">
                <td className="px-4 py-3 font-bold text-primary">
                  <Link href={`/ticker/${r.ticker}`} className="hover:underline">
                    {r.ticker}
                  </Link>
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-3">
                    <span className="w-8 text-right tabular-nums">{r.conviction_score.toFixed(1)}</span>
                    <div className="w-24 h-1.5 bg-muted rounded-full overflow-hidden">
                      <div className="h-full bg-blue-500" style={{ width: `${scorePct}%` }} />
                    </div>
                  </div>
                </td>
                <td className="px-4 py-3 text-right tabular-nums">
                  ${price.toFixed(2)}
                </td>
                <td className="px-4 py-3 text-right tabular-nums text-muted-foreground">
                  ${target.toFixed(2)}
                </td>
                <td className={`px-4 py-3 text-right tabular-nums ${upsideColor}`}>
                  {upside > 0 ? "+" : ""}{upside.toFixed(2)}%
                </td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                    r.analyst_rating > 4 ? "bg-green-500/20 text-green-500" :
                    r.analyst_rating > 2 ? "bg-yellow-500/20 text-yellow-500" :
                    "bg-red-500/20 text-red-500"
                  }`}>
                    {r.analyst_rating > 4 ? "STRONG BUY" : r.analyst_rating > 2 ? "HOLD" : "SELL"}
                  </span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
