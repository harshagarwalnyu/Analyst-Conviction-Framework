import { getTicker, getNews, getRankings } from "@/lib/api";
import { CandlestickChart } from "@/components/CandlestickChart";
import { notFound } from "next/navigation";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";

export default async function TickerPage({ params }: { params: Promise<{ symbol: string }> }) {
  // Await params in Next.js 15
  const { symbol } = await params;
  
  const [ticker, news, rankings] = await Promise.all([
    getTicker(symbol).catch(() => null),
    getNews(symbol).catch(() => []),
    getRankings().catch(() => [])
  ]);

  if (!ticker) return notFound();

  const ranking = rankings.find(r => r.ticker === symbol);

  return (
    <div className="space-y-6 font-mono">
      {/* Header */}
      <div className="flex flex-col gap-4">
        <Link href="/" className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-primary transition-colors">
          <ArrowLeft className="w-4 h-4" /> Back to Rankings
        </Link>
        
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-3xl font-bold text-primary tracking-widest">{ticker.ticker}</h1>
            <h2 className="text-lg text-muted-foreground mt-1">{ticker.name}</h2>
            <div className="flex gap-2 mt-3">
              <span className="bg-muted/50 border border-border/50 px-2 py-0.5 rounded text-xs text-muted-foreground uppercase">{ticker.sector}</span>
              <span className="bg-muted/50 border border-border/50 px-2 py-0.5 rounded text-xs text-muted-foreground uppercase">{ticker.industry}</span>
            </div>
          </div>
          <div className="text-right">
            <div className="text-3xl font-bold tabular-nums text-foreground">${ticker.current_price.toFixed(2)}</div>
            {ranking && (
              <div className="text-sm mt-2 text-muted-foreground flex items-center justify-end gap-2">
                <span>Score:</span>
                <span className="text-primary font-bold bg-primary/10 px-2 py-0.5 rounded">{ranking.conviction_score.toFixed(1)}</span>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Main Chart Column */}
        <div className="xl:col-span-2 space-y-6">
          <div className="h-[400px] border border-border/50 rounded-md bg-card/50 p-1">
             <CandlestickChart symbol={ticker.ticker} />
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <StatBox label="Target Mean" value={`$${ticker.target_mean.toFixed(2)}`} />
            <StatBox label="PEG Ratio" value={ticker.peg_ratio?.toFixed(2) || "N/A"} />
            <StatBox label="Beta" value={ticker.beta?.toFixed(2) || "N/A"} />
            <StatBox label="Total Analysts" value={ticker.total_analysts.toString()} />
            <StatBox label="RSI" value={ticker.rsi?.toFixed(2) || "N/A"} />
            <StatBox label="SMA 50" value={ticker.sma_50 ? `$${ticker.sma_50.toFixed(2)}` : "N/A"} />
            <StatBox label="SMA 200" value={ticker.sma_200 ? `$${ticker.sma_200.toFixed(2)}` : "N/A"} />
            <StatBox label="Avg Sentiment" value={ticker.avg_sentiment.toFixed(2)} />
          </div>
        </div>

        {/* Sidebar Column */}
        <div className="space-y-6">
          {ranking && (
            <div className="border border-border/50 rounded-md bg-card/50 p-5 space-y-4">
              <h3 className="font-bold border-b border-border/50 pb-2 text-primary tracking-widest text-sm">SCORE BREAKDOWN</h3>
              <div className="space-y-3 text-sm">
                {Object.entries(ranking.score_breakdown).map(([key, value]) => (
                  <div key={key} className="flex flex-col gap-1">
                    <div className="flex justify-between items-center">
                      <span className="text-muted-foreground uppercase text-xs tracking-wider">{key.replace(/_/g, " ")}</span>
                      <span className="font-bold tabular-nums text-foreground">{value.toFixed(1)}</span>
                    </div>
                    <div className="h-1 bg-muted rounded-full overflow-hidden">
                      {/* Assuming max score per category is roughly around 25 since there are 4 main categories and total is 100 */}
                      <div className="h-full bg-blue-500/80" style={{ width: `${Math.min(100, Math.max(0, (value / 25) * 100))}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="border border-border/50 rounded-md bg-card/50 p-5 flex flex-col h-[400px]">
            <h3 className="font-bold border-b border-border/50 pb-2 text-primary tracking-widest text-sm shrink-0 mb-4">LATEST NEWS</h3>
            <div className="space-y-4 overflow-y-auto flex-1 pr-2 custom-scrollbar">
              {news.map((item, i) => (
                <div key={i} className="space-y-1.5 pb-4 border-b border-border/30 last:border-0 last:pb-0">
                  <a href={item.link} target="_blank" rel="noopener noreferrer" className="text-sm font-semibold hover:text-blue-400 hover:underline line-clamp-2 leading-snug">
                    {item.title}
                  </a>
                  <div className="text-xs text-muted-foreground flex justify-between uppercase tracking-wider">
                    <span>{item.publisher}</span>
                    <span>{new Date(item.providerPublishTime * 1000).toLocaleDateString()}</span>
                  </div>
                </div>
              ))}
              {news.length === 0 && <p className="text-sm text-muted-foreground text-center py-8">No news available.</p>}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function StatBox({ label, value }: { label: string, value: string }) {
  return (
    <div className="border border-border/50 rounded-md bg-card/50 p-4 hover:border-primary/50 transition-colors">
      <div className="text-[10px] uppercase tracking-widest text-muted-foreground mb-1">{label}</div>
      <div className="text-lg font-bold tabular-nums text-foreground">{value}</div>
    </div>
  );
}
