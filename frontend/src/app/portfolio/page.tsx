import { getPortfolio } from "@/lib/api";

export default async function PortfolioPage() {
  const portfolio = await getPortfolio().catch(() => []);
  
  const activePositions = portfolio.filter(p => p.status === 'open');
  const closedPositions = portfolio.filter(p => p.status === 'closed');
  
  const totalInvested = activePositions.reduce((acc, p) => acc + (p.entry_price * p.shares), 0);
  
  return (
    <div className="space-y-6 font-mono">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-primary">PORTFOLIO</h1>
        <p className="text-sm text-muted-foreground mt-1">Real-time holdings and performance tracking</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="border border-border/50 rounded-md bg-card/50 p-4">
          <div className="text-[10px] uppercase tracking-widest text-muted-foreground mb-1">Total Invested</div>
          <div className="text-2xl font-bold tabular-nums">${totalInvested.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}</div>
        </div>
        <div className="border border-border/50 rounded-md bg-card/50 p-4">
          <div className="text-[10px] uppercase tracking-widest text-muted-foreground mb-1">Active Positions</div>
          <div className="text-2xl font-bold tabular-nums">{activePositions.length}</div>
        </div>
        <div className="border border-border/50 rounded-md bg-card/50 p-4">
          <div className="text-[10px] uppercase tracking-widest text-muted-foreground mb-1">Closed Trades</div>
          <div className="text-2xl font-bold tabular-nums">{closedPositions.length}</div>
        </div>
      </div>

      <div className="border border-border/50 rounded-md bg-card/50 overflow-hidden">
        <div className="bg-muted/30 px-4 py-3 border-b border-border/50 flex justify-between items-center">
          <h2 className="font-bold text-sm tracking-widest text-primary">ACTIVE HOLDINGS</h2>
        </div>
        <div className="p-0 overflow-x-auto">
          <table className="w-full text-sm text-left whitespace-nowrap">
            <thead className="text-xs text-muted-foreground uppercase bg-muted/20 border-b border-border/50">
              <tr>
                <th className="px-4 py-3 font-medium">Ticker</th>
                <th className="px-4 py-3 font-medium">Shares</th>
                <th className="px-4 py-3 font-medium">Entry Date</th>
                <th className="px-4 py-3 font-medium">Entry Price</th>
                <th className="px-4 py-3 font-medium text-right">Entry Score</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/50">
              {activePositions.map((pos, i) => (
                <tr key={i} className="hover:bg-muted/10 transition-colors">
                  <td className="px-4 py-3 font-bold text-primary">{pos.ticker}</td>
                  <td className="px-4 py-3 tabular-nums">{pos.shares}</td>
                  <td className="px-4 py-3 tabular-nums text-muted-foreground">{new Date(pos.entry_date).toLocaleDateString()}</td>
                  <td className="px-4 py-3 tabular-nums">${pos.entry_price.toFixed(2)}</td>
                  <td className="px-4 py-3 tabular-nums text-right">
                    <span className="bg-primary/10 text-primary px-2 py-0.5 rounded">{pos.entry_score.toFixed(1)}</span>
                  </td>
                </tr>
              ))}
              {activePositions.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-center text-muted-foreground">No active positions.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
