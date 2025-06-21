//
//  BatteryCircle.swift
//  VisAssistGlasses
//
//  Created by Trevor Bedson on 6/21/25.
//

import SwiftUI

struct BatteryCircle: View {
    var percentage: CGFloat // 0 to 100

    var body: some View {
        ZStack {
            // Background circle
            Circle()
                .stroke(lineWidth: 10)
                .opacity(0.2)
                .foregroundColor(.green)
            
            // Foreground progress circle
            Circle()
                .trim(from: 1.0 - (percentage / 100), to: 1.0)
                .stroke(style: StrokeStyle(lineWidth: 10, lineCap: .round, lineJoin: .round))
                .foregroundColor(.green)
                .rotationEffect(Angle(degrees: -90))
            
            // Lightning bolt icon
            Image(systemName: "bolt.fill")
                .resizable()
                .scaledToFit()
                .frame(width: 30, height: 30)
                .foregroundColor(.white)
        }
        .frame(width: 100, height: 100)
    }
}
