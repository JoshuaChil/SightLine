//
//  ContentView.swift
//  VisAssistGlasses
//
//  Created by Trevor Bedson on 6/13/25.
//

import SwiftUI
import SwiftData

struct ContentView: View {
    @Environment(\.modelContext) private var modelContext
    
    let tiltFactor = CGFloat(15)
    
    @State private var selectedTab: Tab = .dashboard

    var body: some View {
        ZStack {
            Group {
                switch selectedTab {
                    case .dashboard:
                        DashboardView()
                    case .navigate:
                        NavigateView()
                    case .logs:
                        LogsView()
                    case .help:
                        HelpView()
                    case .settings:
                        SettingsView()
                }
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)

            VStack {
                Spacer()
                
                HStack {
                    TabBarButton(icon: "house.fill", tab: .dashboard, selectedTab: $selectedTab)
                    Spacer()
                    TabBarButton(icon: "map.fill", tab: .navigate, selectedTab: $selectedTab)
                    Spacer()
                    TabBarButton(icon: "newspaper.fill", tab: .logs, selectedTab: $selectedTab)
                    Spacer()
                    TabBarButton(icon: "hand.raised.fill", tab: .help, selectedTab: $selectedTab)
                    Spacer()
                    TabBarButton(icon: "gear", tab: .settings, selectedTab: $selectedTab)
                }
                .padding(.top, 40)
                .padding(.bottom, 20)
                .padding(.horizontal, 20)
                .background(
                    GeometryReader { geometry in
                        let width = geometry.size.width
                        let height = geometry.size.height
                        
                        let top = CGFloat(30)
                        
                        Path { path in
                            path.move(to: CGPoint(x: width, y: height + tiltFactor + top))
                            path.addLine(to: CGPoint(x: 0, y: height + tiltFactor + top))
                            path.addLine(to: CGPoint(x: 0, y: tiltFactor + top))
                            path.addLine(to: CGPoint(x: width, y: top))
                            path.closeSubpath()
                        }
                        .fill(
                            LinearGradient(colors: [Color(hex: "#363E51"), Color(hex: "#181C24")],
                                           startPoint: .top,
                                           endPoint: .bottom)
                        )
                        .frame(height: geometry.size.height + tiltFactor)
                    }
                        .opacity(0.95)
                )
            }
        }
        .ignoresSafeArea(edges: .bottom)
    }
}

enum Tab {
    case dashboard, navigate, logs, help, settings
}

#Preview {
    ContentView()
}
