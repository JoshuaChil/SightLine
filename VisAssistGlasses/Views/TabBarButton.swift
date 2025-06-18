//
//  TabBarButton.swift
//  VisAssistGlasses
//
//  Created by Trevor Bedson on 6/18/25.
//

import SwiftUI

struct TabBarButton: View {
    let icon: String
    let tab: Tab
    @Binding var selectedTab: Tab
    
    var isSelected: Bool {
        selectedTab == tab
    }
    
    var tiltAdjustment: CGFloat {
        switch tab {
            case .dashboard: return CGFloat(0)
            case .navigate: return CGFloat(2)
            case .logs: return CGFloat(4)
            case .help: return CGFloat(6)
            case .settings: return CGFloat(8)
        }
    }

    var body: some View {
        Button(action: {
            withAnimation(.spring()) {
                selectedTab = tab
            }
        }) {
            ZStack {
                // Gradient parallelogram background
                RoundedParallelogram(cornerRadius: 10, slantOffset: 3)
                    .fill(
                        LinearGradient(
                            colors: [Color(hex: "#37B6E9"), Color(hex: "#4B4CED")],
                            startPoint: .top,
                            endPoint: .bottom
                        )
                    )
                    .opacity(isSelected ? 1 : 0)
                    .frame(width: 60, height: 50)
                    .animation(.easeInOut(duration: 0.25), value: isSelected)

                // Icon
                Image(systemName: icon)
                    .font(.system(size: 25, weight: .bold))
                    .foregroundColor(isSelected ? .white : .gray)
                    .scaleEffect(isSelected ? 1.2 : 1.0)
                    .animation(.spring(), value: isSelected)
            }
            .frame(maxWidth: .infinity, minHeight: 45, maxHeight: isSelected ? 60 : 45)
            .offset(y: isSelected ? -(15 + tiltAdjustment) : 0)
            .contentShape(Rectangle())
        }
    }
}

#Preview {
    ContentView()
}
