import Image from 'next/image'
import ResumeMatcher from "@/components/ResumeMatcher";

export default function Home() {
    return (
        <main className="flex min-h-screen flex-col items-center gap-8 p-24">
            <p className='text-4xl font-bold'>Resume Matching</p>
            <ResumeMatcher/>
        </main>
    )
}
