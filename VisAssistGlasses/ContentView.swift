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
        VStack(spacing: 0) {
            Group {
                switch selectedTab {
                case .dashboard:
                    DashboardView()
                default:
                    DashboardView()
                }
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)

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
        .ignoresSafeArea(edges: .bottom)
        .background(ZStack {
            Color.init(hex: "#242C3B")
                .ignoresSafeArea()

            GeometryReader { geometry in
                Path { path in
                    let width = geometry.size.width
                    let height = geometry.size.height

                    path.move(to: CGPoint(x: width, y: height))
                    path.addLine(to: CGPoint(x: width, y: height - 650))
                    path.addLine(to: CGPoint(x: width - 135, y: height - 700))
                    path.addLine(to: CGPoint(x: width - 400, y: height))
                    path.closeSubpath()
                }
                .fill(LinearGradient(colors: [Color.init(hex: "#37B6E9"), Color.init(hex: "#4B4CED")], startPoint: .top, endPoint: .bottom))
            }
            .ignoresSafeArea()
        })
    }
}

enum Tab {
    case dashboard, navigate, logs, help, settings
}

#Preview {
    ContentView()
}
