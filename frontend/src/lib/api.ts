import { components } from "./api.types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export type Ranking = components["schemas"]["RankingSchema"];
export type TickerInfo = components["schemas"]["TickerInfoSchema"];
export type NewsItem = components["schemas"]["NewsItem"];
export type Sector = components["schemas"]["SectorSchema"];
export type PortfolioItem = components["schemas"]["TradeRecordSchema"];

export async function getRankings(): Promise<Ranking[]> {
  const res = await fetch(`${API_BASE}/api/rankings/`, { next: { revalidate: 60 } });
  if (!res.ok) throw new Error("Failed to fetch rankings");
  return res.json();
}

export async function getTicker(symbol: string): Promise<TickerInfo> {
  const res = await fetch(`${API_BASE}/api/ticker/${symbol}`, { next: { revalidate: 60 } });
  if (!res.ok) throw new Error(`Failed to fetch ticker ${symbol}`);
  return res.json();
}

export async function getNews(symbol: string): Promise<NewsItem[]> {
  const res = await fetch(`${API_BASE}/api/news/${symbol}`, { next: { revalidate: 300 } });
  if (!res.ok) throw new Error(`Failed to fetch news for ${symbol}`);
  return res.json();
}

export async function getSectors(): Promise<Sector[]> {
  const res = await fetch(`${API_BASE}/api/sectors/`, { next: { revalidate: 60 } });
  if (!res.ok) throw new Error("Failed to fetch sectors");
  return res.json();
}

export async function getPortfolio(): Promise<PortfolioItem[]> {
  const res = await fetch(`${API_BASE}/api/portfolio/`, { cache: 'no-store' });
  if (!res.ok) throw new Error("Failed to fetch portfolio");
  return res.json();
}
