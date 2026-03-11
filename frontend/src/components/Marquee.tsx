"use client";

import { motion } from "framer-motion";
import { usePriceStream } from "@/hooks/usePriceStream";
import { useMemo } from "react";

export function Marquee({ symbols }: { symbols: string[] }) {
  const prices = usePriceStream(symbols);
  
  const content = useMemo(() => {
    return symbols.map(sym => (
      <div key={sym} className="flex gap-2 items-center mx-4">
        <span className="text-muted-foreground font-mono font-bold">{sym}</span>
        <span className="text-foreground font-mono tabular-nums">
          {prices[sym] ? prices[sym].toFixed(2) : "..."}
        </span>
      </div>
    ));
  }, [symbols, prices]);

  if (symbols.length === 0) return null;

  return (
    <div className="overflow-hidden bg-[#0a0a0b] border-b border-border/50 py-1.5 flex shrink-0">
      <motion.div
        className="flex whitespace-nowrap"
        animate={{ x: [0, -1000] }}
        transition={{ ease: "linear", duration: 20, repeat: Infinity }}
      >
        {content}
        {content}
        {content}
        {content}
        {content}
        {content}
      </motion.div>
    </div>
  );
}
