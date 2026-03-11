import React, { useState, useEffect, useRef, useCallback } from 'react'
import katex from 'katex'
import Plotly from 'plotly.js-dist-min'
import mermaid from 'mermaid'

// ── Mermaid init ──────────────────────────────────────────────────────────────
mermaid.initialize({
  startOnLoad: false,
  theme: 'dark',
  themeVariables: {
    background: '#1a2a3a',
    primaryColor: '#4fc3f7',
    primaryTextColor: '#e8f4fd',
    lineColor: '#4fc3f7',
    secondaryColor: '#0F1929',
    tertiaryColor: '#0a1220',
  },
})

// ── Agent definitions ─────────────────────────────────────────────────────────
const AGENTS = [
  { id: 'guidance_counselor', label: 'Guidance Counselor', emoji: '📚', color: '#7986cb' },
  { id: 'math',               label: 'Math Teacher',        emoji: '➕', color: '#4fc3f7' },
  { id: 'science',            label: 'Science Teacher',     emoji: '🔬', color: '#4db6ac' },
  { id: 'history',            label: 'History Teacher',     emoji: '🏛️', color: '#ff8a65' },
  { id: 'ap_reader',          label: 'AP Reader',           emoji: '📝', color: '#FFD700' },
  { id: 'english',            label: 'English Teacher',     emoji: '✍️', color: '#f48fb1' },
  { id: 'literature',         label: 'Literature Teacher',  emoji: '📖', color: '#ce93d8' },
  { id: 'coping_coach',       label: 'Coping Coach',        emoji: '🧠', color: '#80cbc4' },
  { id: 'tutor',              label: 'Personal Tutor',      emoji: '🎯', color: '#a5d6a7' },
]

const AGENT_MAP = Object.fromEntries(AGENTS.map(a => [a.id, a]))

// ── API base URL — relative when served from Flask, explicit for Electron ─────
// When accessed via browser over the network (http://192.168.x.x:5001), use relative paths.
// When running inside Electron (file:// protocol), fall back to localhost.
const API_BASE = window.location.protocol === 'file:' ? 'http://localhost:5001' : ''

// ── Plotly component ──────────────────────────────────────────────────────────
function PlotlyChart({ spec }) {
  const ref = useRef(null)

  useEffect(() => {
    if (!ref.current) return
    try {
      const parsed = typeof spec === 'string' ? JSON.parse(spec) : spec
      const data = parsed.data || []
      const layout = {
        paper_bgcolor: '#1a2a3a',
        plot_bgcolor: '#0F1929',
        font: { color: '#e8f4fd', family: 'system-ui, sans-serif', size: 13 },
        margin: { t: 40, r: 20, b: 50, l: 50 },
        xaxis: {
          gridcolor: '#2a3a4a',
          zerolinecolor: '#4fc3f7',
          ...(parsed.layout?.xaxis || {}),
        },
        yaxis: {
          gridcolor: '#2a3a4a',
          zerolinecolor: '#4fc3f7',
          ...(parsed.layout?.yaxis || {}),
        },
        ...(parsed.layout || {}),
      }
      const config = { responsive: true, displayModeBar: false }
      Plotly.newPlot(ref.current, data, layout, config)
    } catch (e) {
      console.error('Plotly render error:', e)
      if (ref.current) {
        ref.current.innerHTML = '<p style="color:#ff6b6b;padding:8px">Chart render error</p>'
      }
    }
    return () => {
      if (ref.current) {
        try { Plotly.purge(ref.current) } catch (_) {}
      }
    }
  }, [spec])

  return (
    <div
      ref={ref}
      style={{
        width: '100%',
        minHeight: 300,
        borderRadius: 8,
        overflow: 'hidden',
        marginTop: 8,
        marginBottom: 8,
      }}
    />
  )
}

// ── Mermaid component ─────────────────────────────────────────────────────────
let mermaidCounter = 0
function MermaidDiagram({ code }) {
  const ref = useRef(null)
  const id = useRef(`mermaid-${++mermaidCounter}`)

  useEffect(() => {
    if (!ref.current) return
    const render = async () => {
      try {
        const { svg } = await mermaid.render(id.current, code)
        if (ref.current) ref.current.innerHTML = svg
      } catch (e) {
        console.error('Mermaid render error:', e)
        if (ref.current) ref.current.innerHTML = '<p style="color:#ff6b6b;padding:8px">Diagram render error</p>'
      }
    }
    render()
  }, [code])

  return (
    <div
      ref={ref}
      style={{
        background: '#1a2a3a',
        borderRadius: 8,
        padding: '12px',
        marginTop: 8,
        marginBottom: 8,
        overflowX: 'auto',
      }}
    />
  )
}

// ── Content renderer ──────────────────────────────────────────────────────────
function renderContent(text) {
  if (!text) return null

  const elements = []
  let key = 0

  // Split out code blocks first (plotly, mermaid, generic)
  const codeBlockRegex = /```(\w*)\n([\s\S]*?)```/g
  const parts = []
  let lastIndex = 0
  let match

  while ((match = codeBlockRegex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push({ type: 'text', content: text.slice(lastIndex, match.index) })
    }
    parts.push({ type: 'code_block', lang: match[1], content: match[2].trim() })
    lastIndex = match.index + match[0].length
  }
  if (lastIndex < text.length) {
    parts.push({ type: 'text', content: text.slice(lastIndex) })
  }

  parts.forEach(part => {
    if (part.type === 'code_block') {
      if (part.lang === 'plotly') {
        elements.push(<PlotlyChart key={key++} spec={part.content} />)
      } else if (part.lang === 'mermaid') {
        elements.push(<MermaidDiagram key={key++} code={part.content} />)
      } else {
        elements.push(
          <pre
            key={key++}
            style={{
              background: '#0a1220',
              border: '1px solid #2a3a4a',
              borderRadius: 6,
              padding: '12px 16px',
              overflowX: 'auto',
              fontSize: 13,
              fontFamily: 'Monaco, Menlo, Consolas, monospace',
              color: '#a8d8ea',
              margin: '8px 0',
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word',
            }}
          >
            {part.content}
          </pre>
        )
      }
      return
    }

    // Process inline text (markdown + LaTeX)
    const lines = part.content.split('\n')
    let i = 0

    while (i < lines.length) {
      const line = lines[i]

      // Horizontal rule
      if (/^---+$/.test(line.trim())) {
        elements.push(<hr key={key++} style={{ border: 'none', borderTop: '1px solid #2a3a4a', margin: '12px 0' }} />)
        i++
        continue
      }

      // Heading
      const headingMatch = line.match(/^(#{1,3})\s+(.+)/)
      if (headingMatch) {
        const level = headingMatch[1].length
        const sizes = { 1: 20, 2: 17, 3: 15 }
        elements.push(
          <div
            key={key++}
            style={{
              fontSize: sizes[level] || 15,
              fontWeight: 700,
              color: '#4fc3f7',
              marginTop: level === 1 ? 16 : 12,
              marginBottom: 6,
              borderBottom: level === 1 ? '1px solid #2a3a4a' : 'none',
              paddingBottom: level === 1 ? 6 : 0,
            }}
          >
            {renderInline(headingMatch[2], key)}
          </div>
        )
        i++
        continue
      }

      // Bullet list block
      if (/^[-•*]\s+/.test(line) || /^\d+\.\s+/.test(line)) {
        const listItems = []
        const isOrdered = /^\d+\.\s+/.test(line)
        while (i < lines.length && (/^[-•*]\s+/.test(lines[i]) || /^\d+\.\s+/.test(lines[i]))) {
          const itemText = lines[i].replace(/^[-•*]\s+/, '').replace(/^\d+\.\s+/, '')
          listItems.push(
            <li key={key++} style={{ marginBottom: 4, lineHeight: 1.6 }}>
              {renderInline(itemText, key)}
            </li>
          )
          i++
        }
        const ListTag = isOrdered ? 'ol' : 'ul'
        elements.push(
          <ListTag
            key={key++}
            style={{
              paddingLeft: 22,
              margin: '6px 0',
              color: '#e8f4fd',
            }}
          >
            {listItems}
          </ListTag>
        )
        continue
      }

      // Empty line — spacing
      if (!line.trim()) {
        elements.push(<div key={key++} style={{ height: 6 }} />)
        i++
        continue
      }

      // Normal paragraph
      elements.push(
        <p key={key++} style={{ margin: '4px 0', lineHeight: 1.7, color: '#e8f4fd' }}>
          {renderInline(line, key)}
        </p>
      )
      i++
    }
  })

  return elements
}

// Inline: math, bold, inline code, plain text
function renderInline(text, baseKey) {
  if (!text) return null
  const result = []
  let k = 0

  // Split on $$...$$ (block math), $...$ (inline math), **bold**, `code`
  const pattern = /(\$\$[\s\S]+?\$\$|\$[^$\n]+?\$|\*\*[^*]+\*\*|`[^`]+`)/g
  const segments = text.split(pattern)

  segments.forEach(seg => {
    if (!seg) return

    // Block math $$...$$
    if (seg.startsWith('$$') && seg.endsWith('$$')) {
      const math = seg.slice(2, -2).trim()
      try {
        const html = katex.renderToString(math, { displayMode: true, throwOnError: false, trust: true })
        result.push(
          <span
            key={`${baseKey}-km-${k++}`}
            dangerouslySetInnerHTML={{ __html: html }}
            style={{ display: 'block', overflowX: 'auto', padding: '6px 0' }}
          />
        )
      } catch {
        result.push(<span key={`${baseKey}-km-${k++}`} style={{ color: '#ff6b6b' }}>{seg}</span>)
      }
      return
    }

    // Inline math $...$
    if (seg.startsWith('$') && seg.endsWith('$') && seg.length > 2) {
      const math = seg.slice(1, -1).trim()
      try {
        const html = katex.renderToString(math, { displayMode: false, throwOnError: false, trust: true })
        result.push(
          <span
            key={`${baseKey}-ki-${k++}`}
            dangerouslySetInnerHTML={{ __html: html }}
          />
        )
      } catch {
        result.push(<span key={`${baseKey}-ki-${k++}`} style={{ color: '#ff6b6b' }}>{seg}</span>)
      }
      return
    }

    // Bold **...**
    if (seg.startsWith('**') && seg.endsWith('**')) {
      result.push(
        <strong key={`${baseKey}-b-${k++}`} style={{ color: '#4fc3f7', fontWeight: 700 }}>
          {seg.slice(2, -2)}
        </strong>
      )
      return
    }

    // Inline code `...`
    if (seg.startsWith('`') && seg.endsWith('`')) {
      result.push(
        <code
          key={`${baseKey}-c-${k++}`}
          style={{
            background: '#0a1220',
            border: '1px solid #2a3a4a',
            borderRadius: 4,
            padding: '1px 5px',
            fontSize: '0.88em',
            fontFamily: 'Monaco, Menlo, Consolas, monospace',
            color: '#a8d8ea',
          }}
        >
          {seg.slice(1, -1)}
        </code>
      )
      return
    }

    // Plain text
    result.push(<span key={`${baseKey}-t-${k++}`}>{seg}</span>)
  })

  return result
}

// ── Loading dots ──────────────────────────────────────────────────────────────
function LoadingDots() {
  const [frame, setFrame] = useState(0)
  useEffect(() => {
    const t = setInterval(() => setFrame(f => (f + 1) % 4), 400)
    return () => clearInterval(t)
  }, [])
  const dots = ['●○○', '●●○', '●●●', '○●●'][frame]
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '12px 16px' }}>
      <span style={{ color: '#4fc3f7', fontSize: 18, letterSpacing: 2 }}>{dots}</span>
      <span style={{ color: '#7a9ab8', fontSize: 13 }}>Thinking...</span>
    </div>
  )
}

// ── RHS Assets ────────────────────────────────────────────────────────────────
const RHS_LOGO = 'https://resources.finalsite.net/images/f_auto,q_auto,t_image_size_2/v1718283782/rockwallisdcom/qgnbehenegqggdyoqnmg/RockingRtransparent.png'

const RHS_PHOTOS = [
  'https://resources.finalsite.net/images/f_auto,q_auto,t_image_size_3/v1773081600/rockwallisdcom/gsslpbiiqjjtz6vnk1nx/rhsbanner1.png',
  'https://resources.finalsite.net/images/f_auto,q_auto,t_image_size_3/v1773084668/rockwallisdcom/zvr0g8oiznbcoqh4btud/rhsbanner2_1.png',
  'https://resources.finalsite.net/images/f_auto,q_auto,t_image_size_3/v1773078485/rockwallisdcom/hum3mdfteygk1t7ztlcw/WebsiteGalleryCoverPhoto13.jpg',
  'https://resources.finalsite.net/images/f_auto,q_auto,t_image_size_3/v1772721249/rockwallisdcom/i7wzhcky4wkw6htbg0ho/WebsiteGalleryCoverPhoto12.jpg',
  'https://resources.finalsite.net/images/f_auto,q_auto,t_image_size_3/v1772637156/rockwallisdcom/fv80nm60brluhy8oao7u/WebsiteGalleryCoverPhoto11.jpg',
  'https://resources.finalsite.net/images/f_auto,q_auto,t_image_size_3/v1772553616/rockwallisdcom/q968upqwppptytub1bk7/WebsiteGalleryCoverPhoto10_1.jpg',
  'https://resources.finalsite.net/images/f_auto,q_auto,t_image_size_3/v1771865633/rockwallisdcom/jhvxwtd04ghpbr1iskcb/WebsiteGalleryCoverPhoto9.jpg',
  'https://resources.finalsite.net/images/f_auto,q_auto,t_image_size_3/v1771863130/rockwallisdcom/wugjztwguiuc7mofakhm/WebsiteGalleryCoverPhoto7.jpg',
  'https://resources.finalsite.net/images/f_auto,q_auto,t_image_size_3/v1771865516/rockwallisdcom/f06wek4dgkaowscdfiys/RHSteam.jpg',
  'https://resources.finalsite.net/images/f_auto,q_auto,t_image_size_3/v1772472245/rockwallisdcom/i36pa6cdbqcocs0myftd/rhsbanner.png',
]

// ── Example prompts ───────────────────────────────────────────────────────────
const EXAMPLE_PROMPTS = [
  'Explain the quadratic formula with an example',
  'Help me understand photosynthesis step by step',
  'I have an AP History essay due — can you help me outline it?',
]

// ── Timestamp ─────────────────────────────────────────────────────────────────
function formatTime(ts) {
  return new Date(ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

// ── Main component ────────────────────────────────────────────────────────────
export default function CampusCommand() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [selectedAgent, setSelectedAgent] = useState('')
  const [droppedImage, setDroppedImage] = useState(null) // {data, type, preview}
  const [dragOver, setDragOver] = useState(false)
  const [photoIndex, setPhotoIndex] = useState(0)
  const [showProfile, setShowProfile] = useState(false)
  const [memoryFacts, setMemoryFacts] = useState({})
  const [profileDraft, setProfileDraft] = useState({})
  const [networkUrl, setNetworkUrl] = useState(null)
  const [urlCopied, setUrlCopied] = useState(false)
  const chatEndRef = useRef(null)
  const textareaRef = useRef(null)
  const fileInputRef = useRef(null)

  // Auto-scroll
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  // Rotate welcome photo every 4 seconds
  useEffect(() => {
    const t = setInterval(() => setPhotoIndex(i => (i + 1) % RHS_PHOTOS.length), 4000)
    return () => clearInterval(t)
  }, [])

  // Load student memory on mount
  useEffect(() => {
    fetch(`${API_BASE}/api/memory`)
      .then(r => r.json())
      .then(facts => { setMemoryFacts(facts); setProfileDraft(facts) })
      .catch(() => {})
  }, [])

  // Load network URL for sharing
  useEffect(() => {
    fetch(`${API_BASE}/api/network-url`)
      .then(r => r.json())
      .then(d => { if (d.url) setNetworkUrl(d.url) })
      .catch(() => {})
  }, [])

  // Auto-resize textarea
  const handleInputChange = (e) => {
    setInput(e.target.value)
    const el = e.target
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 120) + 'px'
  }

  // ── Image helpers ────────────────────────────────────────────────────────────
  const readImageFile = (file) => {
    if (!file || !file.type.startsWith('image/')) return
    const reader = new FileReader()
    reader.onload = (e) => {
      const dataURL = e.target.result  // data:image/jpeg;base64,....
      const [header, base64] = dataURL.split(',')
      const mimeMatch = header.match(/data:([^;]+);/)
      setDroppedImage({
        data: base64,
        type: mimeMatch ? mimeMatch[1] : 'image/jpeg',
        preview: dataURL,
        name: file.name,
      })
    }
    reader.readAsDataURL(file)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files[0]
    readImageFile(file)
  }

  const handleDragOver = (e) => { e.preventDefault(); setDragOver(true) }
  const handleDragLeave = () => setDragOver(false)

  // ── Memory helpers ───────────────────────────────────────────────────────────
  const saveFact = async (key, value) => {
    try {
      await fetch(`${API_BASE}/api/memory`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ key, value }),
      })
      setMemoryFacts(prev => {
        const updated = { ...prev }
        if (value) updated[key] = value
        else delete updated[key]
        return updated
      })
    } catch (e) { console.error('Memory save error:', e) }
  }

  const deleteFact = async (key) => {
    try {
      await fetch(`${API_BASE}/api/memory/delete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ key }),
      })
      setMemoryFacts(prev => { const u = { ...prev }; delete u[key]; return u })
      setProfileDraft(prev => { const u = { ...prev }; delete u[key]; return u })
    } catch (e) { console.error('Memory delete error:', e) }
  }

  const sendMessage = useCallback(async (text) => {
    const trimmed = (text || input).trim()
    if ((!trimmed && !droppedImage) || loading) return

    const userMsg = {
      id: Date.now(),
      role: 'user',
      content: trimmed || '📷 Image attached',
      imagePreview: droppedImage?.preview || null,
      timestamp: Date.now(),
    }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setDroppedImage(null)
    setLoading(true)

    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }

    try {
      const contextStr = selectedAgent
        ? `Route to ${selectedAgent} agent. Student specifically selected this agent.`
        : ''

      const body = {
        query: trimmed,
        context: contextStr,
        history: '',
        ...(droppedImage ? { image: { data: droppedImage.data, type: droppedImage.type } } : {}),
      }

      const res = await fetch(`${API_BASE}/api/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })

      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.output || `Server error ${res.status}`)
      }

      const data = await res.json()
      const agentId = (data.notes || '').toLowerCase().replace(/\s+/g, '_') || selectedAgent || 'tutor'
      const agentInfo = AGENT_MAP[agentId] || AGENTS.find(a => (data.notes || '').toLowerCase().includes(a.label.split(' ')[0].toLowerCase())) || AGENTS[8]

      const agentMsg = {
        id: Date.now() + 1,
        role: 'assistant',
        content: data.output || 'No response received.',
        agent: agentInfo.id,
        agentLabel: agentInfo.label,
        agentEmoji: agentInfo.emoji,
        agentColor: agentInfo.color,
        timestamp: Date.now(),
      }
      setMessages(prev => [...prev, agentMsg])
    } catch (e) {
      const errMsg = {
        id: Date.now() + 1,
        role: 'error',
        content: `Connection error: ${e.message}. Make sure the Campus Command server is running.`,
        timestamp: Date.now(),
      }
      setMessages(prev => [...prev, errMsg])
    } finally {
      setLoading(false)
    }
  }, [input, loading, selectedAgent, droppedImage])

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  // ── Styles ──────────────────────────────────────────────────────────────────
  const S = {
    app: {
      display: 'flex',
      flexDirection: 'column',
      height: '100vh',
      width: '100vw',
      background: '#0F1929',
      color: '#e8f4fd',
      overflow: 'hidden',
    },
    header: {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 24px',
      height: 56,
      background: '#0a1220',
      borderBottom: '1px solid #1e3a5a',
      flexShrink: 0,
    },
    headerLeft: {
      display: 'flex',
      alignItems: 'center',
      gap: 12,
    },
    headerTitle: {
      fontSize: 20,
      fontWeight: 800,
      letterSpacing: '0.06em',
      color: '#4fc3f7',
      textTransform: 'uppercase',
    },
    headerBadge: {
      fontSize: 11,
      fontWeight: 600,
      padding: '3px 10px',
      borderRadius: 20,
      background: '#FFD70022',
      border: '1px solid #FFD70060',
      color: '#FFD700',
      letterSpacing: '0.04em',
    },
    body: {
      display: 'flex',
      flex: 1,
      overflow: 'hidden',
    },
    sidebar: {
      width: 188,
      flexShrink: 0,
      background: '#0a1220',
      borderRight: '1px solid #1e3a5a',
      display: 'flex',
      flexDirection: 'column',
      overflowY: 'auto',
      padding: '12px 0',
    },
    sidebarLabel: {
      fontSize: 10,
      fontWeight: 700,
      letterSpacing: '0.12em',
      color: '#4a6a8a',
      textTransform: 'uppercase',
      padding: '0 16px',
      marginBottom: 8,
    },
    agentCard: (agent, isActive) => ({
      display: 'flex',
      alignItems: 'center',
      gap: 9,
      padding: '9px 16px',
      cursor: 'pointer',
      borderLeft: isActive ? `3px solid ${agent.color}` : '3px solid transparent',
      background: isActive ? `${agent.color}18` : 'transparent',
      transition: 'background 0.15s, border-color 0.15s',
    }),
    agentEmoji: {
      fontSize: 16,
      lineHeight: 1,
      flexShrink: 0,
    },
    agentName: (agent, isActive) => ({
      fontSize: 12,
      fontWeight: isActive ? 700 : 400,
      color: isActive ? agent.color : '#8ab0cc',
      lineHeight: 1.3,
    }),
    agentAutoBtn: (isActive) => ({
      display: 'flex',
      alignItems: 'center',
      gap: 9,
      padding: '9px 16px',
      cursor: 'pointer',
      borderLeft: isActive ? '3px solid #4fc3f7' : '3px solid transparent',
      background: isActive ? '#4fc3f718' : 'transparent',
      marginBottom: 8,
    }),
    chatArea: {
      flex: 1,
      display: 'flex',
      flexDirection: 'column',
      overflow: 'hidden',
    },
    messages: {
      flex: 1,
      overflowY: 'auto',
      padding: '24px 28px 12px',
      display: 'flex',
      flexDirection: 'column',
      gap: 4,
    },
    welcomeWrap: {
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      flex: 1,
      gap: 20,
      padding: 40,
    },
    welcomeIcon: {
      fontSize: 56,
      marginBottom: 4,
    },
    welcomeTitle: {
      fontSize: 32,
      fontWeight: 900,
      letterSpacing: '0.08em',
      color: '#4fc3f7',
      textAlign: 'center',
    },
    welcomeSub: {
      fontSize: 15,
      color: '#7a9ab8',
      textAlign: 'center',
    },
    chipRow: {
      display: 'flex',
      flexWrap: 'wrap',
      gap: 10,
      justifyContent: 'center',
      marginTop: 8,
    },
    chip: {
      padding: '8px 16px',
      borderRadius: 20,
      border: '1px solid #2a4a6a',
      background: '#1a2a3a',
      color: '#a8c8e8',
      fontSize: 13,
      cursor: 'pointer',
      transition: 'background 0.15s, border-color 0.15s, color 0.15s',
    },
    userBubbleWrap: {
      display: 'flex',
      justifyContent: 'flex-end',
      marginBottom: 16,
    },
    userBubble: {
      maxWidth: '72%',
      background: '#1565c0',
      borderRadius: '18px 18px 4px 18px',
      padding: '12px 16px',
      fontSize: 14,
      lineHeight: 1.6,
      color: '#e8f4fd',
    },
    userTime: {
      fontSize: 10,
      color: '#90b8d8',
      textAlign: 'right',
      marginTop: 4,
    },
    agentBubbleWrap: {
      display: 'flex',
      justifyContent: 'flex-start',
      marginBottom: 16,
    },
    agentBubbleOuter: (color) => ({
      maxWidth: '78%',
    }),
    agentLabel: (color) => ({
      fontSize: 11,
      fontWeight: 700,
      color: color,
      letterSpacing: '0.04em',
      marginBottom: 4,
      paddingLeft: 2,
    }),
    agentBubble: (color) => ({
      background: '#1a2a3a',
      borderLeft: `3px solid ${color}`,
      borderRadius: '4px 18px 18px 18px',
      padding: '14px 18px',
      fontSize: 14,
      lineHeight: 1.7,
      color: '#e8f4fd',
    }),
    agentTime: {
      fontSize: 10,
      color: '#4a6a8a',
      marginTop: 4,
      paddingLeft: 2,
    },
    errorBubble: {
      background: '#2a0a0a',
      border: '1px solid #c62828',
      borderRadius: 8,
      padding: '10px 14px',
      fontSize: 13,
      color: '#ff6b6b',
      margin: '8px 0',
    },
    inputArea: {
      padding: '14px 20px',
      borderTop: '1px solid #1e3a5a',
      background: '#0a1220',
      flexShrink: 0,
    },
    inputRow: {
      display: 'flex',
      alignItems: 'flex-end',
      gap: 10,
      background: '#1a2a3a',
      border: '1px solid #2a4a6a',
      borderRadius: 16,
      padding: '8px 12px 8px 16px',
    },
    textarea: {
      flex: 1,
      background: 'transparent',
      border: 'none',
      outline: 'none',
      color: '#e8f4fd',
      fontSize: 14,
      lineHeight: 1.6,
      resize: 'none',
      maxHeight: 120,
      minHeight: 24,
      fontFamily: 'inherit',
      padding: 0,
    },
    sendBtn: (disabled) => ({
      width: 36,
      height: 36,
      borderRadius: '50%',
      border: 'none',
      background: disabled ? '#1e3a5a' : '#1565c0',
      color: disabled ? '#4a6a8a' : '#e8f4fd',
      cursor: disabled ? 'not-allowed' : 'pointer',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      flexShrink: 0,
      fontSize: 16,
      transition: 'background 0.15s',
    }),
    agentHint: {
      fontSize: 11,
      color: '#4a6a8a',
      padding: '4px 4px 0',
    },
  }

  const sendDisabled = loading || (!input.trim() && !droppedImage)

  return (
    <div style={S.app}>
      {/* Header */}
      <div style={S.header}>
        <div style={S.headerLeft}>
          <span style={{ fontSize: 24 }}>🎓</span>
          <span style={S.headerTitle}>Campus Command</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          {networkUrl && (
            <button
              onClick={() => {
                navigator.clipboard.writeText(networkUrl).then(() => {
                  setUrlCopied(true)
                  setTimeout(() => setUrlCopied(false), 2000)
                })
              }}
              title="Click to copy — open this address in any browser on the same WiFi"
              style={{
                background: urlCopied ? '#1b5e2022' : '#4fc3f708',
                border: `1px solid ${urlCopied ? '#4caf50' : '#1e3a5a'}`,
                borderRadius: 8,
                color: urlCopied ? '#4caf50' : '#4a6a8a',
                cursor: 'pointer',
                fontSize: 11,
                fontFamily: 'monospace',
                padding: '4px 10px',
                letterSpacing: '0.02em',
                transition: 'all 0.2s',
                flexShrink: 0,
              }}
            >
              {urlCopied ? '✓ Copied!' : '📱 ' + networkUrl}
            </button>
          )}
          <button
            onClick={() => { setProfileDraft({ ...memoryFacts }); setShowProfile(true) }}
            style={{
              background: Object.keys(memoryFacts).length > 0 ? '#4fc3f715' : 'none',
              border: '1px solid #1e3a5a',
              borderRadius: 8,
              color: Object.keys(memoryFacts).length > 0 ? '#4fc3f7' : '#7a9ab8',
              cursor: 'pointer',
              fontSize: 12,
              fontWeight: 600,
              padding: '4px 12px',
              display: 'flex',
              alignItems: 'center',
              gap: 6,
            }}
            title="My Profile & Classes"
          >
            👤 {Object.keys(memoryFacts).length > 0 ? (memoryFacts.student_name || 'My Profile') : 'Set Up Profile'}
          </button>
          <span style={S.headerBadge}>Rockwall ISD · 9th Grade</span>
        </div>
      </div>

      {/* Body */}
      <div style={S.body}>
        {/* Sidebar */}
        <div style={S.sidebar}>
          <div style={S.sidebarLabel}>Agents</div>

          {/* Auto routing option */}
          <div
            style={S.agentAutoBtn(!selectedAgent)}
            onClick={() => setSelectedAgent('')}
            onMouseEnter={e => { if (selectedAgent) e.currentTarget.style.background = '#4fc3f710' }}
            onMouseLeave={e => { if (selectedAgent) e.currentTarget.style.background = 'transparent' }}
          >
            <span style={S.agentEmoji}>🤖</span>
            <span style={{
              fontSize: 12,
              fontWeight: !selectedAgent ? 700 : 400,
              color: !selectedAgent ? '#4fc3f7' : '#8ab0cc',
            }}>
              Auto Route
            </span>
          </div>

          <div style={{ width: '100%', height: 1, background: '#1e3a5a', margin: '4px 0 8px' }} />
          <div style={S.sidebarLabel}>Direct</div>

          {AGENTS.map(agent => {
            const isActive = selectedAgent === agent.id
            return (
              <div
                key={agent.id}
                style={S.agentCard(agent, isActive)}
                onClick={() => setSelectedAgent(isActive ? '' : agent.id)}
                onMouseEnter={e => { if (!isActive) e.currentTarget.style.background = `${agent.color}10` }}
                onMouseLeave={e => { if (!isActive) e.currentTarget.style.background = 'transparent' }}
              >
                <span style={S.agentEmoji}>{agent.emoji}</span>
                <span style={S.agentName(agent, isActive)}>{agent.label}</span>
              </div>
            )
          })}
        </div>

        {/* Chat area */}
        <div
          style={S.chatArea}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
        >
          {/* Drag overlay */}
          {dragOver && (
            <div style={{
              position: 'absolute', inset: 0, zIndex: 10,
              background: 'rgba(15,25,41,0.88)',
              border: '2px dashed #4fc3f7',
              borderRadius: 12,
              display: 'flex', flexDirection: 'column',
              alignItems: 'center', justifyContent: 'center',
              gap: 12, pointerEvents: 'none',
            }}>
              <span style={{ fontSize: 48 }}>📷</span>
              <span style={{ color: '#4fc3f7', fontSize: 18, fontWeight: 700 }}>Drop image here</span>
              <span style={{ color: '#7a9ab8', fontSize: 13 }}>JPG, PNG, or GIF</span>
            </div>
          )}

          <div style={{ ...S.messages, position: 'relative' }}>
            {/* Welcome screen */}
            {messages.length === 0 && !loading && (
              <div style={S.welcomeWrap}>
                {/* Rotating school photo */}
                <div style={{
                  width: '100%', maxWidth: 640, height: 200,
                  borderRadius: 12, overflow: 'hidden',
                  position: 'relative', marginBottom: 8,
                  border: '1px solid #1e3a5a',
                  flexShrink: 0,
                }}>
                  {RHS_PHOTOS.map((src, i) => (
                    <img
                      key={src}
                      src={src}
                      alt="Rockwall High School"
                      style={{
                        position: 'absolute', inset: 0,
                        width: '100%', height: '100%',
                        objectFit: 'cover',
                        opacity: i === photoIndex ? 1 : 0,
                        transition: 'opacity 1s ease',
                      }}
                    />
                  ))}
                  {/* Dark gradient overlay so text stays readable */}
                  <div style={{
                    position: 'absolute', inset: 0,
                    background: 'linear-gradient(to bottom, transparent 40%, rgba(15,25,41,0.85) 100%)',
                  }} />
                  {/* Logo + title over photo */}
                  <div style={{
                    position: 'absolute', bottom: 12, left: 16,
                    display: 'flex', alignItems: 'center', gap: 10,
                  }}>
                    <img src={RHS_LOGO} alt="RHS" style={{ height: 36, width: 'auto', filter: 'drop-shadow(0 1px 3px rgba(0,0,0,0.8))' }} />
                    <div>
                      <div style={{ fontSize: 18, fontWeight: 900, letterSpacing: '0.06em', color: '#fff', textShadow: '0 1px 4px rgba(0,0,0,0.8)' }}>CAMPUS COMMAND</div>
                      <div style={{ fontSize: 11, color: '#c8e8ff', textShadow: '0 1px 3px rgba(0,0,0,0.8)' }}>Rockwall ISD · Rock Nine · Yellowjackets</div>
                    </div>
                  </div>
                </div>

                <div style={S.chipRow}>
                  {EXAMPLE_PROMPTS.map((p, i) => (
                    <div
                      key={i}
                      style={S.chip}
                      onClick={() => sendMessage(p)}
                      onMouseEnter={e => {
                        e.currentTarget.style.background = '#2a3a4a'
                        e.currentTarget.style.borderColor = '#4fc3f7'
                        e.currentTarget.style.color = '#e8f4fd'
                      }}
                      onMouseLeave={e => {
                        e.currentTarget.style.background = '#1a2a3a'
                        e.currentTarget.style.borderColor = '#2a4a6a'
                        e.currentTarget.style.color = '#a8c8e8'
                      }}
                    >
                      {p}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Messages */}
            {messages.map(msg => {
              if (msg.role === 'user') {
                return (
                  <div key={msg.id} style={S.userBubbleWrap}>
                    <div>
                      {msg.imagePreview && (
                        <img
                          src={msg.imagePreview}
                          alt="attached"
                          style={{
                            maxWidth: 260, maxHeight: 200, borderRadius: 10,
                            display: 'block', marginBottom: 6,
                            border: '1px solid #2a4a6a', marginLeft: 'auto',
                          }}
                        />
                      )}
                      {msg.content !== '📷 Image attached' && (
                        <div style={S.userBubble}>{msg.content}</div>
                      )}
                      <div style={S.userTime}>{formatTime(msg.timestamp)}</div>
                    </div>
                  </div>
                )
              }

              if (msg.role === 'error') {
                return (
                  <div key={msg.id} style={S.errorBubble}>{msg.content}</div>
                )
              }

              // Agent message
              const color = msg.agentColor || '#4fc3f7'
              return (
                <div key={msg.id} style={S.agentBubbleWrap}>
                  <div style={S.agentBubbleOuter(color)}>
                    <div style={S.agentLabel(color)}>
                      {msg.agentEmoji} {msg.agentLabel}
                    </div>
                    <div style={S.agentBubble(color)}>
                      {renderContent(msg.content)}
                    </div>
                    <div style={S.agentTime}>{formatTime(msg.timestamp)}</div>
                  </div>
                </div>
              )
            })}

            {/* Loading indicator */}
            {loading && (
              <div style={S.agentBubbleWrap}>
                <div>
                  <div style={S.agentLabel('#4fc3f7')}>
                    {selectedAgent
                      ? `${AGENT_MAP[selectedAgent]?.emoji} ${AGENT_MAP[selectedAgent]?.label}`
                      : '🎓 Campus Command'}
                  </div>
                  <div style={{ ...S.agentBubble('#4fc3f7'), padding: '4px 8px' }}>
                    <LoadingDots />
                  </div>
                </div>
              </div>
            )}

            <div ref={chatEndRef} />
          </div>

          {/* Input */}
          <div style={S.inputArea}>
            {selectedAgent && (
              <div style={S.agentHint}>
                Sending directly to {AGENT_MAP[selectedAgent]?.emoji} {AGENT_MAP[selectedAgent]?.label} — click Auto Route in sidebar to remove
              </div>
            )}

            {/* Image preview strip */}
            {droppedImage && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
                <img
                  src={droppedImage.preview}
                  alt="preview"
                  style={{
                    height: 56, width: 'auto', maxWidth: 120,
                    borderRadius: 8, border: '1px solid #2a4a6a', objectFit: 'cover',
                  }}
                />
                <span style={{ fontSize: 12, color: '#7a9ab8', flex: 1 }}>{droppedImage.name}</span>
                <button
                  onClick={() => setDroppedImage(null)}
                  style={{
                    background: 'none', border: 'none', color: '#ff6b6b',
                    cursor: 'pointer', fontSize: 16, padding: '0 4px',
                  }}
                  title="Remove image"
                >✕</button>
              </div>
            )}

            <div style={S.inputRow}>
              {/* Hidden file input */}
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                style={{ display: 'none' }}
                onChange={e => readImageFile(e.target.files[0])}
              />
              {/* Image upload button */}
              <button
                style={{
                  background: 'none', border: 'none',
                  color: droppedImage ? '#4fc3f7' : '#4a6a8a',
                  cursor: 'pointer', fontSize: 18, padding: '0 4px',
                  flexShrink: 0,
                }}
                onClick={() => fileInputRef.current?.click()}
                title="Attach image (or drag & drop)"
                disabled={loading}
              >
                📷
              </button>
              <textarea
                ref={textareaRef}
                style={S.textarea}
                value={input}
                onChange={handleInputChange}
                onKeyDown={handleKeyDown}
                placeholder={droppedImage ? 'Add a question about this image… (or just press Enter)' : 'Ask anything — math, science, history, essays, or just talk…'}
                rows={1}
                disabled={loading}
              />
              <button
                style={S.sendBtn(sendDisabled)}
                onClick={() => sendMessage()}
                disabled={sendDisabled}
                title="Send (Enter)"
              >
                ▶
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* ── My Profile Modal ─────────────────────────────────────────────────── */}
      {showProfile && (
        <div
          style={{
            position: 'fixed', inset: 0, zIndex: 1000,
            background: 'rgba(0,0,0,0.75)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}
          onClick={() => setShowProfile(false)}
        >
          <div
            style={{
              background: '#0F1929',
              border: '1px solid #1e3a5a',
              borderRadius: 16,
              width: 500, maxWidth: '92vw',
              maxHeight: '85vh',
              overflowY: 'auto',
              padding: 28,
            }}
            onClick={e => e.stopPropagation()}
          >
            {/* Modal header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
              <span style={{ fontSize: 18, fontWeight: 700, color: '#4fc3f7' }}>👤 My Profile</span>
              <button onClick={() => setShowProfile(false)} style={{ background: 'none', border: 'none', color: '#7a9ab8', fontSize: 20, cursor: 'pointer' }}>✕</button>
            </div>
            <p style={{ color: '#7a9ab8', fontSize: 12, marginBottom: 20, lineHeight: 1.5 }}>
              Everything saved here is remembered permanently across sessions — all agents will know your context automatically.
            </p>

            {/* Pre-defined fields */}
            {[
              { key: 'student_name',    label: 'Your Name',              placeholder: 'e.g. Alex',                                                       multi: false },
              { key: 'current_classes', label: 'Current Classes',        placeholder: 'e.g. Algebra I, English I Honors, AP Human Geography, Biology',   multi: true  },
              { key: 'ap_classes',      label: 'AP / Honors Classes',    placeholder: 'e.g. AP Human Geography, English I Honors',                       multi: false },
              { key: 'learning_goals',  label: 'Learning Goals',         placeholder: 'e.g. Improve essay writing, understand quadratic equations',      multi: false },
              { key: 'teachers',        label: 'Teacher Names',          placeholder: 'e.g. Ms. Smith (Math), Mr. Jones (English)',                      multi: false },
            ].map(({ key, label, placeholder, multi }) => (
              <div key={key} style={{ marginBottom: 16 }}>
                <div style={{ fontSize: 12, fontWeight: 600, color: '#8ab0cc', marginBottom: 6 }}>{label}</div>
                {multi ? (
                  <textarea
                    value={profileDraft[key] || ''}
                    onChange={e => setProfileDraft(d => ({ ...d, [key]: e.target.value }))}
                    placeholder={placeholder}
                    rows={3}
                    style={{
                      width: '100%', boxSizing: 'border-box',
                      background: '#0a1220', border: '1px solid #1e3a5a',
                      borderRadius: 8, color: '#e8f4fd', fontSize: 13,
                      padding: '8px 12px', resize: 'vertical', fontFamily: 'inherit',
                    }}
                  />
                ) : (
                  <input
                    type="text"
                    value={profileDraft[key] || ''}
                    onChange={e => setProfileDraft(d => ({ ...d, [key]: e.target.value }))}
                    placeholder={placeholder}
                    style={{
                      width: '100%', boxSizing: 'border-box',
                      background: '#0a1220', border: '1px solid #1e3a5a',
                      borderRadius: 8, color: '#e8f4fd', fontSize: 13,
                      padding: '8px 12px', fontFamily: 'inherit',
                    }}
                  />
                )}
              </div>
            ))}

            {/* Extra stored facts not in the predefined list */}
            {(() => {
              const predefined = ['student_name','current_classes','ap_classes','learning_goals','teachers']
              const extras = Object.entries(memoryFacts).filter(([k]) => !predefined.includes(k))
              if (extras.length === 0) return null
              return (
                <div style={{ marginBottom: 16 }}>
                  <div style={{ fontSize: 12, fontWeight: 600, color: '#8ab0cc', marginBottom: 8 }}>Other Saved Facts</div>
                  {extras.map(([k, v]) => (
                    <div key={k} style={{
                      display: 'flex', alignItems: 'center', gap: 8,
                      background: '#0a1220', border: '1px solid #1e3a5a',
                      borderRadius: 8, padding: '6px 12px', marginBottom: 6, fontSize: 12,
                    }}>
                      <span style={{ color: '#4fc3f7', fontWeight: 600 }}>{k}:</span>
                      <span style={{ color: '#e8f4fd', flex: 1 }}>{v}</span>
                      <button onClick={() => deleteFact(k)} style={{ background: 'none', border: 'none', color: '#ff6b6b', cursor: 'pointer', fontSize: 14 }}>✕</button>
                    </div>
                  ))}
                </div>
              )
            })()}

            {/* Save button */}
            <button
              onClick={async () => {
                const predefined = ['student_name','current_classes','ap_classes','learning_goals','teachers']
                for (const key of predefined) {
                  const draftVal = (profileDraft[key] || '').trim()
                  const storedVal = (memoryFacts[key] || '').trim()
                  if (draftVal !== storedVal) await saveFact(key, draftVal)
                }
                setShowProfile(false)
              }}
              style={{
                width: '100%',
                background: '#1565c0',
                border: 'none',
                borderRadius: 10,
                color: '#e8f4fd',
                fontSize: 14,
                fontWeight: 700,
                padding: '11px 0',
                cursor: 'pointer',
                marginTop: 4,
              }}
            >
              Save Profile
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
