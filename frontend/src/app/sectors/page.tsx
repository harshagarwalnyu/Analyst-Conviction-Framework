import { getSectors } from "@/lib/api";

export default async function SectorsPage() {
  const sectors = await getSectors().catch(() => []);

  return (
    <div className="space-y-6 font-mono">
      <div>
        <h1 className="text-2xl font-bold font-mono tracking-tight text-primary">SECTOR ANALYSIS</h1>
        <p className="text-sm text-muted-foreground mt-1">Aggregated conviction scores and performance by sector</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {sectors.map((sector, i) => (
          <div key={i} className="border border-border/50 rounded-md bg-card/50 p-5 hover:border-primary/50 transition-colors">
            <h3 className="font-bold text-foreground text-lg">{sector.sector}</h3>
            <div className="mt-4 flex justify-between items-center">
              <div className="flex flex-col">
                <span className="text-[10px] uppercase text-muted-foreground tracking-widest">Avg Score</span>
                <span className={`text-xl font-bold tabular-nums ${sector.avg_score > 60 ? 'text-green-500' : sector.avg_score < 40 ? 'text-red-500' : 'text-yellow-500'}`}>
                  {sector.avg_score.toFixed(1)}
                </span>
              </div>
              <div className="flex flex-col text-right">
                <span className="text-[10px] uppercase text-muted-foreground tracking-widest">Tickers</span>
                <span className="text-xl font-bold tabular-nums text-foreground">{sector.ticker_count}</span>
              </div>
            </div>
            <div className="mt-4 h-1.5 w-full bg-muted rounded-full overflow-hidden">
              <div 
                className={`h-full ${sector.avg_score > 60 ? 'bg-green-500' : sector.avg_score < 40 ? 'bg-red-500' : 'bg-yellow-500'}`} 
                style={{ width: `${Math.min(100, sector.avg_score)}%` }} 
              />
            </div>
          </div>
        ))}
        {sectors.length === 0 && (
          <div className="col-span-full p-8 text-center text-muted-foreground border border-border/50 rounded bg-card/50">
            No sector data available.
          </div>
        )}
      </div>
    </div>
  );
}
