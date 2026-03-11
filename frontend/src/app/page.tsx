import { getRankings } from "@/lib/api";
import { RankingsTable } from "@/components/RankingsTable";
import { components } from "@/lib/api.types";

export const revalidate = 60; // revalidate every 60 seconds

export default async function Home() {
  let rankings: components["schemas"]["RankingSchema"][] = [];
  try {
    rankings = await getRankings();
  } catch (error) {
    console.error("Failed to load rankings:", error);
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold font-mono tracking-tight text-primary">TOP OPPORTUNITIES</h1>
        <p className="text-sm text-muted-foreground font-mono mt-1">Quantitatively scored and ranked equities</p>
      </div>
      
      {rankings.length > 0 ? (
        <RankingsTable initialRankings={rankings} />
      ) : (
        <div className="p-8 text-center text-muted-foreground font-mono border border-border/50 rounded bg-card/50">
          Unable to load rankings. Ensure the backend is running.
        </div>
      )}
    </div>
  );
}
