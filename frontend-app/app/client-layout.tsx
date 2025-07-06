"use client"

import { ThemeProvider } from "next-themes"
import { MainLayout } from "@/components/layout/main-layout"
import { useEffect, useState } from "react"

export default function ClientLayout({ children }: { children: React.ReactNode }) {
  const [mounted, setMounted] = useState(false)

  // Prevent hydration mismatch by only rendering the theme provider on the client
  useEffect(() => {
    setMounted(true)
  }, [])

  if (!mounted) {
    // Return a simple layout without theme provider during SSR
    return (
      <div className="min-h-screen bg-background">
        <div className="container mx-auto p-4">
          {children}
        </div>
      </div>
    )
  }

  return (
    <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
      <MainLayout>{children}</MainLayout>
    </ThemeProvider>
  )
}
