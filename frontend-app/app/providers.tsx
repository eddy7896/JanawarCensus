"use client"

import { ThemeProvider } from "next-themes"
import { MainLayout } from "@/components/layout/main-layout"
import { ReactNode } from "react"

interface ProvidersProps {
  children: ReactNode
}

export default function Providers({ children }: ProvidersProps) {
  return (
    <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
      <MainLayout>{children}</MainLayout>
    </ThemeProvider>
  )
}

export { Providers }
