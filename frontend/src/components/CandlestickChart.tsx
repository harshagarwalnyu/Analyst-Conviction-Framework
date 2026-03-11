"use client";

import { useEffect, useRef } from "react";
import { createChart, ColorType, CrosshairMode, CandlestickSeries } from "lightweight-charts";

export function CandlestickChart({ symbol }: { symbol: string }) {
  const chartContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!chartContainerRef.current) return;

    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: "#a1a1aa", // text-muted-foreground
        fontFamily: "monospace",
      },
      grid: {
        vertLines: { color: "#27272a" }, // border-border
        horzLines: { color: "#27272a" },
      },
      crosshair: {
        mode: CrosshairMode.Normal,
      },
      timeScale: {
        borderColor: "#27272a",
      },
      rightPriceScale: {
        borderColor: "#27272a",
      },
    });

    const candlestickSeries = chart.addSeries(CandlestickSeries, {
      upColor: "#22c55e",
      downColor: "#ef4444",
      borderVisible: false,
      wickUpColor: "#22c55e",
      wickDownColor: "#ef4444",
    });

    // Generate some dummy historical data for demonstration
    const data = [];
    let currentPrice = 100 + Math.random() * 50;
    const today = new Date();
    today.setHours(0,0,0,0);
    
    for (let i = 100; i >= 0; i--) {
      const time = new Date(today);
      time.setDate(time.getDate() - i);
      
      const open = currentPrice;
      const close = open + (Math.random() - 0.5) * 5;
      const high = Math.max(open, close) + Math.random() * 2;
      const low = Math.min(open, close) - Math.random() * 2;
      
      data.push({
        time: time.toISOString().split('T')[0],
        open,
        high,
        low,
        close,
      });
      currentPrice = close;
    }

    candlestickSeries.setData(data);

    const handleResize = () => {
      if (chartContainerRef.current) {
        chart.applyOptions({ width: chartContainerRef.current.clientWidth });
      }
    };

    window.addEventListener("resize", handleResize);
    handleResize();

    return () => {
      window.removeEventListener("resize", handleResize);
      chart.remove();
    };
  }, [symbol]);

  return <div ref={chartContainerRef} className="w-full h-full" />;
}
