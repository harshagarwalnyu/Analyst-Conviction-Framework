import type { Metadata } from "next";
import localFont from "next/font/local";
import "./globals.css";
import { cn } from "@/lib/utils";
import { Marquee } from "@/components/Marquee";
import Link from "next/link";
import { BarChart2, Briefcase, Settings, Search, PieChart, Activity } from "lucide-react";

const geistSans = localFont({
  src: "./fonts/GeistVF.woff",
  variable: "--font-geist-sans",
  weight: "100 900",
});
const geistMono = localFont({
  src: "./fonts/GeistMonoVF.woff",
  variable: "--font-geist-mono",
  weight: "100 900",
});

export const metadata: Metadata = {
  title: "Terminal",
  description: "Stock Market Analyst Terminal",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={cn("dark font-sans", geistMono.variable, geistSans.variable)}>
      <body className="antialiased bg-[#0a0a0b] text-foreground flex flex-col h-screen overflow-hidden">
        {/* Top Navbar */}
        <header className="h-12 border-b border-border/50 flex items-center justify-between px-4 bg-[#0a0a0b] shrink-0">
          <div className="flex items-center gap-6">
            <span className="font-bold text-primary tracking-widest">TERMINAL</span>
            <div className="relative flex items-center">
              <Search className="absolute left-2 w-4 h-4 text-muted-foreground" />
              <input 
                className="bg-muted/30 border border-border/50 rounded-md pl-8 pr-2 py-1 text-sm outline-none focus:ring-1 focus:ring-primary font-mono w-64 transition-all"
                placeholder="Search ticker..."
              />
            </div>
          </div>
          <div className="text-xs font-mono text-muted-foreground">
            {new Date().toISOString().split("T")[0]} MARKET OPEN
          </div>
        </header>

        {/* Marquee */}
        <Marquee symbols={["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA", "BRK.B", "LLY", "V"]} />

        <div className="flex flex-1 overflow-hidden">
          {/* Sidebar */}
          <aside className="w-16 sm:w-48 border-r border-border/50 flex flex-col items-center sm:items-start py-4 gap-2 bg-[#0a0a0b] shrink-0">
            <Link href="/" className="flex items-center gap-3 px-4 py-2 hover:bg-muted/30 rounded-md w-full text-sm transition-colors group">
              <BarChart2 className="w-4 h-4 text-muted-foreground group-hover:text-primary transition-colors" />
              <span className="hidden sm:inline font-mono">Rankings</span>
            </Link>
            <Link href="/sectors" className="flex items-center gap-3 px-4 py-2 hover:bg-muted/30 rounded-md w-full text-sm transition-colors group">
              <PieChart className="w-4 h-4 text-muted-foreground group-hover:text-primary transition-colors" />
              <span className="hidden sm:inline font-mono text-muted-foreground group-hover:text-foreground transition-colors">Sectors</span>
            </Link>
            <Link href="/portfolio" className="flex items-center gap-3 px-4 py-2 hover:bg-muted/30 rounded-md w-full text-sm transition-colors group">
              <Briefcase className="w-4 h-4 text-muted-foreground group-hover:text-primary transition-colors" />
              <span className="hidden sm:inline font-mono text-muted-foreground group-hover:text-foreground transition-colors">Portfolio</span>
            </Link>
            <Link href="/backtest" className="flex items-center gap-3 px-4 py-2 hover:bg-muted/30 rounded-md w-full text-sm transition-colors group">
              <Activity className="w-4 h-4 text-muted-foreground group-hover:text-primary transition-colors" />
              <span className="hidden sm:inline font-mono text-muted-foreground group-hover:text-foreground transition-colors">Backtest</span>
            </Link>
            <div className="mt-auto w-full">
              <Link href="/settings" className="flex items-center gap-3 px-4 py-2 hover:bg-muted/30 rounded-md w-full text-sm transition-colors group">
                <Settings className="w-4 h-4 text-muted-foreground group-hover:text-primary transition-colors" />
                <span className="hidden sm:inline font-mono text-muted-foreground group-hover:text-foreground transition-colors">Settings</span>
              </Link>
            </div>
          </aside>

          {/* Main Content */}
          <main className="flex-1 overflow-y-auto p-4 sm:p-6 bg-[#0a0a0b]">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
