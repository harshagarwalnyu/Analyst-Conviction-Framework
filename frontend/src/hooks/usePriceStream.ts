"use client";

import { useState, useEffect } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export function usePriceStream(symbols: string[]) {
  const [prices, setPrices] = useState<Record<string, number>>({});

  // Stringify for dependency array
  const symbolsKey = symbols.join(",");

  useEffect(() => {
    if (!symbolsKey) return;

    const url = new URL(`${API_BASE}/api/stream/prices`);
    url.searchParams.append("symbols", symbolsKey);

    const eventSource = new EventSource(url.toString());

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setPrices((prev) => ({ ...prev, ...data }));
      } catch (error) {
        console.error("Failed to parse SSE message", error);
      }
    };

    eventSource.onerror = (error) => {
      console.error("SSE Error", error);
      eventSource.close();
    };

    return () => {
      eventSource.close();
    };
  }, [symbolsKey]);

  return prices;
}
